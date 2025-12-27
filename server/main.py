import os
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

from server.core_models.model_registry import get_model_class, MODEL_REGISTRY
from server.core_models.validation import validate_create_body, validate_predict_body
from server.models.linear_regression_model import LinearRegressionModel
from server.core_models.logger import get_logger

# ------------------------------------------------
# Environment
# ------------------------------------------------
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)

# ------------------------------------------------
# Logger
# ------------------------------------------------
logger = get_logger("api")

# ------------------------------------------------
# App
# ------------------------------------------------
app = FastAPI(
    title="Linear Regression Trainer API",
    description="Train and predict ML models",
    version="1.0.0"
)


# ------------------------------------------------
# Middleware
# ------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# ------------------------------------------------
# Startup
# ------------------------------------------------
@app.on_event("startup")
def startup_event():
    logger.info("API started successfully")


# ------------------------------------------------
# Routes
# ------------------------------------------------
@app.get("/")
def home():
    logger.info("Health check endpoint called")
    return {"message": "Trainer API is running"}


# -------------------------------
# /create → train model
# -------------------------------
@app.post("/create")
async def create_model(request: Request):
    try:
        body = await request.json()
        validate_create_body(body)

        model_name = body.get("model_name", "linear")  # default to linear
        modelClass = get_model_class(model_name)
        model = modelClass()
        logger.info(f"Starting training model: {model_name}")

        metrics = model.train(
            csv_file=body["csv_file"],
            feature_cols=body["feature_cols"],
            label_col=body["label_col"],
            train_percentage=body["train_percentage"]
        )

        logger.info(f"Training completed successfully {model_name}")
        return {"status": "success", "metrics": metrics}

    except KeyError as e:
        logger.error(str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error during training")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# /predict/{model_name} → predict
# -------------------------------
@app.post("/predict/{model_name}")
async def predict_model(model_name: str, request: Request):
    try:
        if any(x in model_name for x in ("/", "\\", "..")):
            raise HTTPException(status_code=400, detail="Invalid model name")

        body = await request.json()
        logger.info(f"Validating /predict input for model: {model_name}")
        validate_predict_body(body)

        modelClass = get_model_class(model_name)
        model = modelClass()

        prediction = model.predict(body["features"])

        logger.info(f"Prediction successful: {prediction}")
        return {"status": "success", "prediction": prediction}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        logger.warning(f"Model not found: {model_name}")
        raise HTTPException(status_code=404, detail="Model not found")

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Prediction error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
def list_supported_models():
    """
    Returns a list of supported models
    """
    supported_models = list(MODEL_REGISTRY.keys())
    logger.info(f"Supported models requested: {supported_models}")
    return {"supported_models": supported_models}