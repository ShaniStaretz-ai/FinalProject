from server.models.knn_model import KNNModel
from server.models.linear_regression_model import LinearRegressionModel


# Map model_type string to Trainer class
MODEL_CLASSES = {
    "linear": LinearRegressionModel,
    "knn": KNNModel,
    # Add new models here
}