"""
Model training and prediction routes.
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends, status
from fastapi.concurrency import run_in_threadpool
from sklearn.utils._param_validation import InvalidParameterError

from server.config import TRAIN_MODELS_DIR
from server.models.model_classes import MODEL_CLASSES
from server.models.base_trainer import BaseTrainer
from server.security.jwt_auth import get_current_user
from server.users.repository import check_and_deduct_tokens, get_user_id_by_email
from server.models.repository import create_model_record, get_user_models, get_model_by_name

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["models"]
)

# -----------------------------
# Helper functions
# -----------------------------
def parse_csv(upload_file: UploadFile) -> pd.DataFrame:
    """
    Reads an uploaded CSV file and returns a pandas DataFrame.
    Raises HTTPException on errors.
    """
    try:
        contents = upload_file.file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        # Reset pointer in case file is read again
        upload_file.file.seek(0)
        df = pd.read_csv(upload_file.file)
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file has no data")
        return df
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.exception("Failed to read CSV")
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {e}")

def parse_json_param(param: str, param_name: str) -> Any:
    """
    Parses a JSON string parameter and raises HTTPException if invalid.
    For 'feature_cols', also accepts comma-separated string format as fallback.
    """
    try:
        return json.loads(param)
    except json.JSONDecodeError:
        # Special handling for feature_cols: accept comma-separated string
        if param_name == "feature_cols":
            # Try to parse as comma-separated string
            if isinstance(param, str) and not param.startswith('['):
                # Split by comma and strip whitespace
                return [col.strip() for col in param.split(',') if col.strip()]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON in parameter '{param_name}'. Expected JSON format (e.g., [\"age\",\"salary\"] for feature_cols)"
        )

def validate_optional_params(trainer_cls, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filters the optional parameters to include only valid keys defined in trainer_cls.OPTIONAL_PARAMS.
    """
    allowed_params = getattr(trainer_cls, "OPTIONAL_PARAMS", {})
    invalid_keys = [k for k in params.keys() if k not in allowed_params]
    if invalid_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid optional parameter(s): {invalid_keys}"
        )
    return {k: params[k] for k in params if k in allowed_params}


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
    Requires authentication.
    """
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    models = get_user_models(user_id)
    return [model["model_name"] for model in models]


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

    # Validate columns
    missing_cols = [c for c in feature_cols_list + [label_col] if c not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Columns not found in CSV: {missing_cols}")

    # Validate model type
    if model_type not in MODEL_CLASSES:
        raise HTTPException(status_code=400, detail=f"Model type '{model_type}' not recognized")

    trainer_cls = MODEL_CLASSES[model_type]
    valid_optional_params = validate_optional_params(trainer_cls, optional_params_dict)

    # All validations passed - now check and deduct tokens
    check_and_deduct_tokens(current_user, TRAINING_TOKEN_COST)

    # Get user ID for model tracking
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

    # Initialize and train in threadpool (async safe)
    try:
        trainer = trainer_cls(model_name=model_name, **valid_optional_params)
        metrics = await run_in_threadpool(trainer.train, df, feature_cols_list, label_col, train_percentage)
        
        # Store model record in database
        # Use full path for file_path to match where the model is actually saved
        model_path = str(Path(TRAIN_MODELS_DIR) / f"{model_name}.pkl")
        model_id = create_model_record(user_id, model_name, model_type, model_path)
        if model_id is None:
            logger.warning(f"Failed to create model record for {model_name}, but model was trained successfully")
        
    except InvalidParameterError as e:
        raise HTTPException(status_code=400, detail=f"Invalid model parameter: {e}")
    except Exception as e:
        logger.exception("Training failed")
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")

    return {"status": "success", "model_name": model_name, "metrics": metrics, "tokens_deducted": TRAINING_TOKEN_COST}


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
    check_and_deduct_tokens(current_user, PREDICTION_TOKEN_COST)

    trainer = trainer_cls(model_name=model_name, **valid_optional_params)
    try:
        prediction = trainer.predict(features)
        return {"status": "success", "prediction": prediction, "tokens_deducted": PREDICTION_TOKEN_COST}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model file not found: {model_name}")
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

