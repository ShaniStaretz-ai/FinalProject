from fastapi import FastAPI, HTTPException, Request
from server.models.model_registry import MODEL_CLASSES
from server.models.base_trainer import BaseTrainer
import os

app = FastAPI(title="Trainer API", version="1.0.0")

@app.get("/trained_models")
def get_trained_models():
    from server.config import TRAIN_MODELS_DIR
    models = [f.replace(".pkl","") for f in os.listdir(TRAIN_MODELS_DIR) if f.endswith(".pkl")]
    return {"trained_models": models}

@app.post("/create")
async def create_model(request: Request):
    body = await request.json()
    required_params = ["model_type", "model_name", "csv_file", "feature_cols", "label_col"]
    missing = [p for p in required_params if p not in body]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required parameters: {', '.join(missing)}")

    model_type = body.pop("model_type").lower()
    model_name = body.pop("model_name")
    csv_file = body.pop("csv_file")
    feature_cols = body.pop("feature_cols")
    label_col = body.pop("label_col")
    train_percentage = body.pop("train_percentage", 0.8)
    optional_params = body  # any extra parameters

    if model_type not in MODEL_CLASSES:
        raise HTTPException(status_code=400, detail=f"Unsupported model type: {model_type}")

    trainer_class = MODEL_CLASSES[model_type]
    trainer = trainer_class(model_name=model_name, **optional_params)
    metrics = trainer.train(csv_file, feature_cols, label_col, train_percentage)
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
