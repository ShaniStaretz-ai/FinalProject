import logging
import os
import sys
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

from server.models.linear_regression_model import train_linear_regression_model,predict

# Load environment variables from .env file
# Load from project root (one level up from server/)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# Get log level from environment variable, default to DEBUG
log_level_str = os.getenv("LOG_LEVEL", "DEBUG").upper()
log_level = getattr(logging, log_level_str, logging.DEBUG)

# Configure logging to go to stdout immediately
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # ensures it overwrites existing configs
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Also configure uvicorn loggers to show our app logs
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_error_logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Linear Regression Trainer API",
              description="Train and save models via API",
              version="1.0.0")
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

@app.on_event("startup")
def startup_event():
    logger.info(f"App is starting... Log level: {log_level_str}")
    logger.debug("Logger: App startup event")


@app.get("/")
def home():
    print("Endpoint '/' called",flush=True)  # May not always appear with --reload
    logger.info("Endpoint '/' called")
    return {"message": "Trainer API is running!"}

# -------------------------------
# /create → train and save model
# -------------------------------
@app.post("/create")
async def create_model(request: Request):
    """
    Train a Linear Regression model using parameters in JSON body.
    """
    try:
        logger.info(f"start create model")
        body = await request.json()
        print(body)
        required = ["csv_file", "feature_cols", "label_col", "train_percentage", "model_filename"]
        missing = [k for k in required if k not in body]
        if missing:
            logger.error(f"missing parameters in the body request")
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
            # CSV file exists check

        if not os.path.exists(body["csv_file"]):
            raise HTTPException(status_code=400, detail=f"File not found: {body['csv_file']}")


        metrics = train_linear_regression_model(**body)
        return {"status": "success", "metrics": metrics}

    except Exception as e:
        logger.error(f"error in create model: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------
# /predict/{model_name} → load model and predict
# -------------------------------
@app.post("/predict/{model_name}")
async def predict_model(model_name: str, request: Request):
    """
    Load a trained model and predict using input features.
    Path parameter: model_name (e.g., "linear")
    Example body:
    {
      "features": {
        "age": 30,
        "salary": 50000,
        "city": "Chicago",
        "hire_date": 1583020800
      }
    }
    """
    try:
        logger.info(f"Predict request received for model: {model_name}")
        body = await request.json()
        features = body.get("features")
        if not features:
            logger.error("Missing 'features' in request body")
            raise ValueError("'features' is required in the request body.")
        
        # Convert model_name to model_filename (add .pkl extension)
        model_filename = f"{model_name}.pkl"
        logger.info(f"Loading model: {model_filename}")
        
        # Predict
        prediction = predict(model_filename, features)
        logger.info(f"Prediction successful: {prediction}")

        return {"status": "success", "prediction": prediction}

    except FileNotFoundError as e:
        logger.error(f"Model file not found: {model_filename}")
        raise HTTPException(status_code=404, detail=f"Model file not found: {model_filename}")
    except Exception as e:
        logger.error(f"Error in predict_model: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))