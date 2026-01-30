from sklearn.linear_model import LinearRegression
from server.ml.base_trainer import BaseTrainer


class LinearRegressionModel(BaseTrainer):
    OPTIONAL_PARAMS = {
        "fit_intercept": "bool",
    }

    def __init__(self, model_name: str = "linear_regression", fit_intercept: bool = True, **kwargs):
        model = LinearRegression(fit_intercept=fit_intercept)
        super().__init__(model_name, model=model, **kwargs)
