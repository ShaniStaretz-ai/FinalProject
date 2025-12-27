from models.linear_regression_model import LinearRegressionModel
from models.knn_model import KNNModel

# Registry: model_name -> class
MODEL_REGISTRY = {
    "linear": LinearRegressionModel,
    "knn": KNNModel
}

def get_model_class(model_name: str):
    """
    Returns the model class for the given model_name.
    Raises KeyError if model not found.
    """
    if model_name not in MODEL_REGISTRY:
        raise KeyError(f"Model '{model_name}' is not registered")
    return MODEL_REGISTRY[model_name]