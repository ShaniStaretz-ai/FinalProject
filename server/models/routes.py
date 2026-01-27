"""
Model training and prediction routes.
"""
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends, status
from fastapi.concurrency import run_in_threadpool
from sklearn.utils._param_validation import InvalidParameterError

from server.config import TRAIN_MODELS_DIR
from server.models.model_classes import MODEL_CLASSES
from server.models.base_trainer import BaseTrainer
from server.models.helpers import parse_csv, parse_json_param, validate_optional_params
from server.security.jwt_auth import get_current_user
from server.users.repository import check_and_deduct_tokens, get_user_id_by_email, get_user_tokens, update_user_tokens
from server.models.repository import create_model_record, get_user_models, get_model_by_name, delete_model

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["models"]
)


# -----------------------------
# Endpoints
# -----------------------------
@router.get("/models")
async def get_models() -> Dict[str, Dict[str, Any]]:
    """
    Returns a dict of all supported models with optional parameters.
    """
    return {name: {"params": getattr(cls, "OPTIONAL_PARAMS", {})} for name, cls in sorted(MODEL_CLASSES.items())}


@router.get("/trained")
async def get_trained_models(current_user: str = Depends(get_current_user)) -> List[str]:
    """
    Returns the list of trained model names for the authenticated user.
    Only returns models whose files actually exist on disk.
    Requires authentication.
    """
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    models = get_user_models(user_id)
    # Filter to only include models whose files exist
    valid_model_names = []
    for model in models:
        file_path = model.get("file_path")
        if file_path and os.path.exists(file_path):
            valid_model_names.append(model["model_name"])
        else:
            logger.warning(f"Model {model['model_name']} has database record but file not found at {file_path}")
    
    logger.info(f"User {current_user} retrieved {len(valid_model_names)} trained model(s) (out of {len(models)} in database)")
    return valid_model_names


@router.get("/trained/{model_name}")
async def get_model_details(
    model_name: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific trained model, including feature columns.
    Requires authentication and model ownership.
    """
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Sanitize model_name to prevent path traversal
    safe_model_name = re.sub(r'[^a-zA-Z0-9_-]', '', model_name)
    if safe_model_name != model_name:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name: contains illegal characters"
        )
    
    model_record = get_model_by_name(user_id, safe_model_name)
    if model_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found or you don't have access to it"
        )
    
    # Verify file exists
    file_path = model_record.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model file not found for '{model_name}'"
        )
    
    # Parse feature_cols from JSON string
    feature_cols_str = model_record.get("feature_cols")
    feature_cols = []
    
    if feature_cols_str:
        # Handle empty string, None, or invalid JSON
        feature_cols_str = feature_cols_str.strip()
        if feature_cols_str and feature_cols_str != '':
            try:
                feature_cols = json.loads(feature_cols_str)
                # Ensure it's a list
                if not isinstance(feature_cols, list):
                    feature_cols = []
            except (json.JSONDecodeError, TypeError):
                feature_cols = []
    
    # Log if feature_cols is empty (for debugging)
    if not feature_cols:
        logger.warning(f"Model {model_name} has no feature_cols stored (may be an older model)")
    
    return {
        "model_name": model_record["model_name"],
        "model_type": model_record["model_type"],
        "feature_cols": feature_cols,
        "created_at": str(model_record["created_at"])
    }


@router.delete("/delete/{model_name}")
async def delete_model_endpoint(
    model_name: str,
    current_user: str = Depends(get_current_user)
):
    """
    Delete a trained model by name.
    Requires authentication and only allows deletion of models owned by the authenticated user.
    Deletes both the database record and associated files from disk.
    """
    # Sanitize model_name to prevent path traversal
    safe_model_name = re.sub(r'[^a-zA-Z0-9_-]', '', model_name)
    if safe_model_name != model_name:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name: contains illegal characters"
        )
    
    # Get user ID and verify model ownership
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify model exists and belongs to user
    model_record = get_model_by_name(user_id, model_name)
    if model_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found or you don't have access to it"
        )
    
    # Delete the model (database record and files)
    logger.info(f"User {current_user} (ID: {user_id}) deleting model: {model_name}")
    success = delete_model(user_id, model_name)
    if not success:
        logger.error(f"Model deletion failed: {model_name} for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model '{model_name}'"
        )
    
    logger.info(f"Model deleted successfully: {model_name} by user {current_user}")
    return {"status": "success", "message": f"Model '{model_name}' deleted successfully"}


@router.post("/create")
async def create_model(
    model_type: str = Form(...),
    feature_cols: str = Form(...),
    label_col: str = Form(...),
    train_percentage: float = Form(0.8),
    csv_file: Optional[UploadFile] = File(None),
    optional_params: str = Form("{}"),
    model_filename: Optional[str] = Form(None),
    current_user: str = Depends(get_current_user)
):
    """
    Train a new ML model.
    Requires authentication and deducts 1 token after validation passes.
    
    If model_filename is provided, it will be used (sanitized and prefixed with user_id).
    If not provided, a unique name will be auto-generated with timestamp.
    """
    TRAINING_TOKEN_COST = 1
    
    # Validate inputs first
    if csv_file is None:
        raise HTTPException(status_code=400, detail="CSV file missing")
    
    # Validate train_percentage range
    if not (0 < train_percentage < 1):
        raise HTTPException(status_code=400, detail="train_percentage must be between 0 and 1")

    df = await run_in_threadpool(parse_csv, csv_file)
    feature_cols_list = parse_json_param(feature_cols, "feature_cols")
    optional_params_dict = parse_json_param(optional_params, "optional_params")

    # Validate feature_cols_list is not empty
    if not feature_cols_list or len(feature_cols_list) == 0:
        raise HTTPException(status_code=400, detail="feature_cols cannot be empty")

    # Validate columns
    missing_cols = [c for c in feature_cols_list + [label_col] if c not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Columns not found in CSV: {missing_cols}")

    # Validate model type
    if model_type not in MODEL_CLASSES:
        raise HTTPException(status_code=400, detail=f"Model type '{model_type}' not recognized")

    trainer_cls = MODEL_CLASSES[model_type]
    valid_optional_params = validate_optional_params(trainer_cls, optional_params_dict)

    # Get user ID for model tracking (before token deduction)
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Generate model name: use provided filename or auto-generate
    if model_filename:
        # Sanitize the provided filename
        # Remove path separators and dangerous characters, keep only alphanumeric, underscore, hyphen
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', model_filename)
        safe_name = safe_name.strip('_')  # Remove leading/trailing underscores
        if not safe_name:
            raise HTTPException(status_code=400, detail="Invalid model filename")
        # Prefix with user_id to ensure uniqueness and ownership
        model_name = f"{user_id}_{safe_name}"
    else:
        # Auto-generate unique name with timestamp (including microseconds for uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        model_name = f"{user_id}_{model_type}_{timestamp}"

    # All validations passed - now check and deduct tokens
    # Tokens are deducted here, but if training fails, we'll need to refund them
    logger.info(f"Starting model training: {model_name} (type: {model_type}, user: {current_user})")
    check_and_deduct_tokens(current_user, TRAINING_TOKEN_COST)
    tokens_deducted = True

    # Initialize and train in threadpool (async safe)
    try:
        trainer = trainer_cls(model_name=model_name, **valid_optional_params)
        metrics = await run_in_threadpool(trainer.train, df, feature_cols_list, label_col, train_percentage)
        
        # Store model record in database
        # Use full path for file_path to match where the model is actually saved
        model_path = str(Path(TRAIN_MODELS_DIR) / f"{model_name}.pkl")
        
        # Verify model file was actually saved
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file was not saved to expected path: {model_path}")
        
        # Store feature_cols as JSON string
        feature_cols_json = json.dumps(feature_cols_list)
        model_id = create_model_record(user_id, model_name, model_type, model_path, feature_cols_json)
        if model_id is None:
            logger.warning(f"Failed to create model record for {model_name}, but model was trained successfully")
        
        logger.info(f"Model training completed: {model_name} (R²={metrics['r2_score']:.3f}, user: {current_user}, saved to: {model_path})")
        
    except InvalidParameterError as e:
        # Refund tokens if training fails due to invalid parameters
        if tokens_deducted:
            current_tokens = get_user_tokens(current_user)
            if current_tokens is not None:
                update_user_tokens(current_user, current_tokens + TRAINING_TOKEN_COST)
                logger.info(f"Refunded {TRAINING_TOKEN_COST} tokens to {current_user} due to training failure")
        raise HTTPException(status_code=400, detail=f"Invalid model parameter: {e}")
    except Exception as e:
        # Refund tokens if training fails
        if tokens_deducted:
            current_tokens = get_user_tokens(current_user)
            if current_tokens is not None:
                update_user_tokens(current_user, current_tokens + TRAINING_TOKEN_COST)
                logger.info(f"Refunded {TRAINING_TOKEN_COST} tokens to {current_user} due to training failure")
        logger.exception("Training failed")
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")

    return {
        "status": "success",
        "model_name": model_name,
        "metrics": metrics,
        "tokens_deducted": TRAINING_TOKEN_COST,
        "file_path": model_path,
        "saved_location": "server/train_models folder"
    }


@router.post("/predict/{model_name}")
async def predict_model(
    model_name: str,
    request: Request,
    current_user: str = Depends(get_current_user)
):
    """
    Make a prediction using a trained model.
    Requires authentication and deducts 5 tokens after validation passes.
    Only allows prediction on models owned by the authenticated user.
    """
    PREDICTION_TOKEN_COST = 5
    
    # Sanitize model_name to prevent path traversal
    # Model names should only contain alphanumeric, underscore, hyphen, and match the pattern user_id_*
    safe_model_name = re.sub(r'[^a-zA-Z0-9_-]', '', model_name)
    if safe_model_name != model_name:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name: contains illegal characters"
        )
    
    # Get user ID and verify model ownership
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    model_record = get_model_by_name(user_id, model_name)
    if model_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found or you don't have access to it"
        )
    
    # Validate inputs first
    body = await request.json()
    features = body.get("features")
    if not features:
        raise HTTPException(status_code=400, detail="Missing 'features' in request body")
    optional_params = {k: v for k, v in body.items() if k != "features"}

    # Use model_type from database record
    model_type = model_record["model_type"]
    trainer_cls = MODEL_CLASSES.get(model_type, BaseTrainer)
    
    # Validate optional parameters
    valid_optional_params = validate_optional_params(trainer_cls, optional_params)

    # All validations passed - now check and deduct tokens
    logger.info(f"Prediction request: model={model_name}, user={current_user}, features={len(features)}")
    check_and_deduct_tokens(current_user, PREDICTION_TOKEN_COST)

    trainer = trainer_cls(model_name=model_name, **valid_optional_params)
    try:
        prediction = trainer.predict(features)
        logger.info(f"Prediction successful: model={model_name}, user={current_user}, prediction={prediction:.4f}")
        return {"status": "success", "prediction": prediction, "tokens_deducted": PREDICTION_TOKEN_COST}
    except FileNotFoundError:
        logger.exception("Prediction failed: model file not found")
        raise HTTPException(status_code=404, detail=f"Model file not found: {model_name}")
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

