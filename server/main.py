import os
import shutil
import tempfile
from io import StringIO, BytesIO
from pathlib import Path
import pandas as pd
import json
from fastapi import FastAPI, HTTPException, Request,UploadFile, File, Form
from server.config import TRAIN_MODELS_DIR
from server.models.model_classes import MODEL_CLASSES
from server.models.base_trainer import BaseTrainer


app = FastAPI(title="Trainer API", version="1.0.0")

# -----------------------------
# Return all supported models + optional parameters
# -----------------------------
@app.get("/models")
async def get_models():
    """
    Returns a dict of all supported models with optional parameters.
    Example:
    {
        "knn": {"params": {"n_neighbors": "int", "weights": "str"}},
        "random_forest": {"params": {"n_estimators": "int"}}
    }
    """
    models_info = {}
    for name, cls in MODEL_CLASSES.items():
        models_info[name] = {"params": getattr(cls, "OPTIONAL_PARAMS", {})}
    return models_info


# -----------------------------
# Return trained models
# -----------------------------


@app.get("/trained")
async def get_trained_models():
    """
    Returns the list of trained model filenames (without extensions/timestamps)
    """
    p = Path(TRAIN_MODELS_DIR)
    models = [f.stem for f in p.glob("*.pkl")]
    return models

from typing import Optional
@app.post("/create")
async def create_model(
        model_type: str = Form(...),
        feature_cols: str = Form(...),
        label_col: str = Form(...),
        train_percentage: float = Form(0.8),
        csv_file: Optional[UploadFile] = File(None),
        optional_params: str = Form("{}")
):
    if csv_file is None:
        raise HTTPException(status_code=400, detail="CSV file missing")

    # Read the uploaded file content into memory
    try:
        contents = await csv_file.read()  # async read
        csv_file.file.seek(0)  # reset pointer
        if not contents:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        # Decode bytes to string if necessary
        if isinstance(contents, bytes):
            contents = contents.decode("utf-8")

        df = pd.read_csv(StringIO(contents))
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {e}")

    # Parse JSON strings
    try:
        feature_cols = json.loads(feature_cols)
        optional_params = json.loads(optional_params)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in feature_cols or optional_params")

    # Validate columns
    missing_cols = [c for c in feature_cols + [label_col] if c not in df.columns]
    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Columns not found in CSV: {missing_cols}")

    # Initialize trainer
    if model_type not in MODEL_CLASSES:
        raise HTTPException(status_code=400, detail=f"Model type '{model_type}' not recognized")

    trainer_class = MODEL_CLASSES[model_type]
    trainer = trainer_class(**optional_params)

    # Train
    metrics = trainer.train(df, feature_cols, label_col, train_percentage)

    return {"status": "success", "metrics": metrics}

@app.post("/predict/{model_name}")
async def predict_model(model_name: str, request: Request):
    body = await request.json()
    features = body.get("features")
    if not features:
        raise HTTPException(status_code=400, detail="Missing 'features' in request body")
    optional_params = {k:v for k,v in body.items() if k != "features"}

    # Infer type from model_name
    model_type = None
    for key in MODEL_CLASSES.keys():
        if model_name.lower().startswith(key):
            model_type = key
            break
    if model_type:
        trainer_class = MODEL_CLASSES[model_type]
        trainer = trainer_class(model_name=model_name, **optional_params)
    else:
        trainer = BaseTrainer(model_name=model_name)
    try:
        prediction = trainer.predict(features)
        return {"status": "success", "prediction": prediction}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")
