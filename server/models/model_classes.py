from server.models.knn_model import KNNModel
from server.models.linear_regression_model import LinearRegressionModel
from server.models.logistic_model import LogisticModel
from server.models.random_forest_model import RandomForestModel

MODEL_CLASSES = {
    "knn": KNNModel,
    "linear": LinearRegressionModel,
    "logistic": LogisticModel,
    "random_forest": RandomForestModel,
}

def get_model_class(model_name: str):
    """
    Returns the model class for the given model_name.
    Raises KeyError if model not found.
    """
    if model_name not in MODEL_CLASSES:
        raise KeyError(f"Model '{model_name}' is not registered")
    return MODEL_CLASSES[model_name]