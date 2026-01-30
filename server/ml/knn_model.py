from sklearn.neighbors import KNeighborsRegressor
from server.ml.base_trainer import BaseTrainer


class KNNModel(BaseTrainer):
    OPTIONAL_PARAMS = {
        "n_neighbors": "int",
        "weights": "str",
    }

    def __init__(self, model_name: str = "knn", n_neighbors: int = 5, weights: str = "uniform", **kwargs):
        model = KNeighborsRegressor(n_neighbors=n_neighbors, weights=weights)
        super().__init__(model_name, model=model, **kwargs)
