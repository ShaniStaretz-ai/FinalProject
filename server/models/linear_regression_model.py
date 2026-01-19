from sklearn.linear_model import LinearRegression
from server.models.base_trainer import BaseTrainer

class LinearRegressionModel(BaseTrainer):
    OPTIONAL_PARAMS = {
        "fit_intercept": "bool",
    }
    
    def __init__(self, model_name: str = "linear_regression", fit_intercept: bool = True, **kwargs):
        model = LinearRegression(fit_intercept=fit_intercept)
        super().__init__(model_name, model=model, **kwargs)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    model = LinearRegressionModel("LinearRegression")

    metrics = model.train(
        csv_file="../../employees.csv",
        feature_cols=["age", "salary", "city", "hire_date"],
        label_col="bonus",
        train_percentage=0.8
    )

    prediction = model.predict({
        "age": 30,
        "salary": 50000,
        "city": "Chicago",
        "hire_date": 1583020800
    })

    logger.info(f"Metrics: {metrics}")
    logger.info(f"Prediction: {prediction}")