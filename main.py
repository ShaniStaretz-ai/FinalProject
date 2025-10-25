import logging
import sys
from fastapi import FastAPI, Request, HTTPException

from linear_regression_model import train_linear_regression_model,predict

# Configure logging to go to stdout immediately
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True  # ensures it overwrites existing configs
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Linear Regression Trainer API",
              description="Train and save models via API",
              version="1.0.0")
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.on_event("startup")
def startup_event():
    print("App is starting...")
    logger.info("Logger: App startup event")


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

        required = ["csv_file", "feature_cols", "label_col", "train_percentage", "model_filename", "col_types"]
        missing = [k for k in required if k not in body]
        if missing:
            logger.error(f"missing parameters in the body request")
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        metrics = train_linear_regression_model(**body)
        return {"status": "success", "metrics": metrics}

    except Exception as e:
        logger.error("error in create model:",str(e))
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------
# /predict → load model and predict
# -------------------------------
@app.post("/predict")
async def predict_model(request: Request):
    """
    Load a trained model and predict using input features.
    Example body:
    {
      "model_filename": "linear.pkl",
      "features": {
        "age": 30,
        "salary": 50000,
        "city_Chicago": 0,
        "city_Houston": 1,
        "city_Los Angeles": 0,
        "hire_date": 1583020800
      }
    }
    """
    try:
        print(f"start predict_model")
        body = await request.json()
        print(f"receive body:",body)
        model_filename = body.get("model_filename")
        print("model_filename:",model_filename)
        features = body.get("features")
        col_types = body.get("col_types")
        print(features)
        if not model_filename or not features or not col_types:
            raise ValueError("Both 'model_filename' and 'features' are required.")


        # Predict
        prediction = predict(model_filename,features,col_types)

        return {"status": "success", "prediction": prediction}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model file not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))