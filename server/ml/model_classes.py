from server.ml.knn_model import KNNModel
from server.ml.linear_regression_model import LinearRegressionModel
from server.ml.logistic_model import LogisticModel
from server.ml.random_forest_model import RandomForestModel

MODEL_CLASSES = {
    "knn": KNNModel,
    "linear": LinearRegressionModel,
    "logistic": LogisticModel,
    "random_forest": RandomForestModel,
}


def get_model_class(model_name: str):
    if model_name not in MODEL_CLASSES:
        raise KeyError(f"Model '{model_name}' is not registered")
    return MODEL_CLASSES[model_name]
