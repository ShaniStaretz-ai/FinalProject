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

from server.config import TRAIN_MODELS_DIR, METRICS_DIR
from server.ml import MODEL_CLASSES
from server.ml.base_trainer import BaseTrainer
from server.ml.helpers import parse_csv, parse_json_param, validate_optional_params
from server.security.jwt_auth import get_current_user
from server.users.repository import check_and_deduct_tokens, get_user_id_by_email, refund_tokens
from server.models.repository import create_model_record, get_user_models, get_model_by_name, delete_model

logger = logging.getLogger(__name__)

router = APIRouter(tags=["models"])


@router.get("/models")
async def get_models() -> Dict[str, Dict[str, Any]]:
    return {name: {"params": getattr(cls, "OPTIONAL_PARAMS", {})} for name, cls in sorted(MODEL_CLASSES.items())}


@router.get("/trained")
async def get_trained_models(current_user: str = Depends(get_current_user)) -> List[str]:
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    models = get_user_models(user_id)
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
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
    file_path = model_record.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model file not found for '{model_name}'"
        )
    feature_cols_str = model_record.get("feature_cols")
    feature_cols = []
    
    if feature_cols_str:
        feature_cols_str = feature_cols_str.strip()
        if feature_cols_str and feature_cols_str != '':
            try:
                feature_cols = json.loads(feature_cols_str)
                if not isinstance(feature_cols, list):
                    feature_cols = []
            except (json.JSONDecodeError, TypeError):
                feature_cols = []
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
    safe_model_name = re.sub(r'[^a-zA-Z0-9_-]', '', model_name)
    if safe_model_name != model_name:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name: contains illegal characters"
        )
    
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found"        )
    model_record = get_model_by_name(user_id, model_name)
    if model_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found or you don't have access to it"
        )
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
    TRAINING_TOKEN_COST = 1
    if csv_file is None:
        raise HTTPException(status_code=400, detail="CSV file missing")
    if not (0 < train_percentage < 1):
        raise HTTPException(status_code=400, detail="train_percentage must be between 0 and 1")

    df = await run_in_threadpool(parse_csv, csv_file)
    feature_cols_list = parse_json_param(feature_cols, "feature_cols")
    optional_params_dict = parse_json_param(optional_params, "optional_params")
    if not feature_cols_list or len(feature_cols_list) == 0:
        raise HTTPException(status_code=400, detail="feature_cols cannot be empty")
    missing_cols = [c for c in feature_cols_list + [label_col] if c not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Columns not found in CSV: {missing_cols}")

    # Validate data: no missing values in label column or selected feature columns
    if df[label_col].isna().any():
        raise HTTPException(
            status_code=400,
            detail=f"Label column '{label_col}' contains missing values. Please clean your data before training."
        )
    feature_na = df[feature_cols_list].isna().any()
    cols_with_na = [col for col, has_na in feature_na.items() if has_na]
    if cols_with_na:
        raise HTTPException(
            status_code=400,
            detail=f"Feature column(s) {cols_with_na} contain missing values. Please clean or impute them before training."
        )

    if model_type not in MODEL_CLASSES:
        raise HTTPException(status_code=400, detail=f"Model type '{model_type}' not recognized")

    trainer_cls = MODEL_CLASSES[model_type]
    valid_optional_params = validate_optional_params(trainer_cls, optional_params_dict)
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if model_filename:
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', model_filename)
        safe_name = safe_name.strip('_')
        if not safe_name:
            raise HTTPException(status_code=400, detail="Invalid model filename")
        model_name = f"{user_id}_{safe_name}"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        model_name = f"{user_id}_{model_type}_{timestamp}"
    logger.info(f"Starting model training: {model_name} (type: {model_type}, user: {current_user})")
    tokens_deducted = False
    model_path = None
    try:
        check_and_deduct_tokens(current_user, TRAINING_TOKEN_COST)
        tokens_deducted = True
        trainer = trainer_cls(model_name=model_name, **valid_optional_params)
        metrics = await run_in_threadpool(trainer.train, df, feature_cols_list, label_col, train_percentage)
        model_path = str(Path(TRAIN_MODELS_DIR) / f"{model_name}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file was not saved to expected path: {model_path}")
        feature_cols_json = json.dumps(feature_cols_list)
        model_id = create_model_record(user_id, model_name, model_type, model_path, feature_cols_json)
        if model_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Model name already exists or failed to save record."
            )
        logger.info(
            f"Training results for {model_name} (user: {current_user}): "
            f"R²={metrics.get('r2_score', 0):.4f}, MSE={metrics.get('mean_squared_error', 0):.4f}, "
            f"MAE={metrics.get('mean_absolute_error', 0):.4f}; saved to {model_path}"
        )
        
    except HTTPException:
        if tokens_deducted and model_path and os.path.exists(model_path):
            try:
                os.remove(model_path)
                logger.info(f"Removed orphaned model file: {model_path}")
            except OSError as err:
                logger.warning(f"Could not remove orphaned model file {model_path}: {err}")
            metrics_path = os.path.join(METRICS_DIR, f"{model_name}_metrics.json")
            if os.path.exists(metrics_path):
                try:
                    os.remove(metrics_path)
                    logger.info(f"Removed orphaned metrics file: {metrics_path}")
                except OSError as err:
                    logger.warning(f"Could not remove orphaned metrics file {metrics_path}: {err}")
        if tokens_deducted:
            if refund_tokens(current_user, TRAINING_TOKEN_COST):
                logger.info(f"Refunded {TRAINING_TOKEN_COST} tokens to {current_user} due to training failure")
        raise
    except InvalidParameterError as e:
        if tokens_deducted and model_path and os.path.exists(model_path):
            try:
                os.remove(model_path)
                logger.info(f"Removed orphaned model file: {model_path}")
            except OSError as err:
                logger.warning(f"Could not remove orphaned model file {model_path}: {err}")
            metrics_path = os.path.join(METRICS_DIR, f"{model_name}_metrics.json")
            if os.path.exists(metrics_path):
                try:
                    os.remove(metrics_path)
                except OSError:
                    pass
        if tokens_deducted:
            if refund_tokens(current_user, TRAINING_TOKEN_COST):
                logger.info(f"Refunded {TRAINING_TOKEN_COST} tokens to {current_user} due to training failure")
        raise HTTPException(status_code=400, detail=f"Invalid model parameter: {e}")
    except Exception as e:
        if tokens_deducted and model_path and os.path.exists(model_path):
            try:
                os.remove(model_path)
                logger.info(f"Removed orphaned model file: {model_path}")
            except OSError as err:
                logger.warning(f"Could not remove orphaned model file {model_path}: {err}")
            metrics_path = os.path.join(METRICS_DIR, f"{model_name}_metrics.json")
            if os.path.exists(metrics_path):
                try:
                    os.remove(metrics_path)
                except OSError:
                    pass
        if tokens_deducted:
            if refund_tokens(current_user, TRAINING_TOKEN_COST):
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
    PREDICTION_TOKEN_COST = 5
    safe_model_name = re.sub(r'[^a-zA-Z0-9_-]', '', model_name)
    if safe_model_name != model_name:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name: contains illegal characters"
        )
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    model_record = get_model_by_name(user_id, model_name)
    if model_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found or you don't have access to it"
        )
    body = await request.json()
    features = body.get("features")
    if not features:
        raise HTTPException(status_code=400, detail="Missing 'features' in request body")
    model_type = model_record["model_type"]
    trainer_cls = MODEL_CLASSES.get(model_type, BaseTrainer)
    logger.info(f"Prediction request: model={model_name}, user={current_user}, features={len(features)}")
    tokens_deducted = False
    try:
        check_and_deduct_tokens(current_user, PREDICTION_TOKEN_COST)
        tokens_deducted = True
        trainer = trainer_cls(model_name=model_name)
        prediction = trainer.predict(features)
        logger.info(f"Prediction successful: model={model_name}, user={current_user}, prediction={prediction:.4f}")
        return {"status": "success", "prediction": prediction, "tokens_deducted": PREDICTION_TOKEN_COST}
    except HTTPException:
        if tokens_deducted and refund_tokens(current_user, PREDICTION_TOKEN_COST):
            logger.info(f"Refunded {PREDICTION_TOKEN_COST} tokens to {current_user} due to prediction failure")
        raise
    except FileNotFoundError:
        if tokens_deducted and refund_tokens(current_user, PREDICTION_TOKEN_COST):
            logger.info(f"Refunded {PREDICTION_TOKEN_COST} tokens to {current_user} due to prediction failure (model file not found)")
        logger.exception("Prediction failed: model file not found")
        raise HTTPException(status_code=404, detail=f"Model file not found: {model_name}")
    except Exception as e:
        if tokens_deducted and refund_tokens(current_user, PREDICTION_TOKEN_COST):
            logger.info(f"Refunded {PREDICTION_TOKEN_COST} tokens to {current_user} due to prediction failure")
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

