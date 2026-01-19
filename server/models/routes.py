"""
Model training and prediction routes.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from sklearn.utils._param_validation import InvalidParameterError

from server.config import TRAIN_MODELS_DIR
from server.models.model_classes import MODEL_CLASSES
from server.models.base_trainer import BaseTrainer

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
    """
    try:
        return json.loads(param)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON in parameter '{param_name}'"
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
async def get_trained_models() -> List[str]:
    """
    Returns the list of trained model filenames (without extensions/timestamps)
    """
    p = Path(TRAIN_MODELS_DIR)
    if not p.exists():
        return []
    return [f.stem for f in p.glob("*.pkl")]


@router.post("/create")
async def create_model(
    model_type: str = Form(...),
    feature_cols: str = Form(...),
    label_col: str = Form(...),
    train_percentage: float = Form(0.8),
    csv_file: Optional[UploadFile] = File(None),
    optional_params: str = Form("{}")
):
    """
    Train a new ML model.
    """
    if csv_file is None:
        raise HTTPException(status_code=400, detail="CSV file missing")

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

    # Initialize and train in threadpool (async safe)
    try:
        trainer = trainer_cls(**valid_optional_params)
        metrics = await run_in_threadpool(trainer.train, df, feature_cols_list, label_col, train_percentage)
    except InvalidParameterError as e:
        raise HTTPException(status_code=400, detail=f"Invalid model parameter: {e}")
    except Exception as e:
        logger.exception("Training failed")
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")

    return {"status": "success", "metrics": metrics}


@router.post("/predict/{model_name}")
async def predict_model(model_name: str, request: Request):
    """
    Make a prediction using a trained model.
    """
    body = await request.json()
    features = body.get("features")
    if not features:
        raise HTTPException(status_code=400, detail="Missing 'features' in request body")
    optional_params = {k: v for k, v in body.items() if k != "features"}

    # Infer model type
    model_type = next((k for k in MODEL_CLASSES.keys() if model_name.lower().startswith(k)), None)
    trainer_cls = MODEL_CLASSES.get(model_type, BaseTrainer)
    valid_optional_params = validate_optional_params(trainer_cls, optional_params)

    trainer = trainer_cls(model_name=model_name, **valid_optional_params)
    try:
        prediction = trainer.predict(features)
        return {"status": "success", "prediction": prediction}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

