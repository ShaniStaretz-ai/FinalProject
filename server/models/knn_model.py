from sklearn.neighbors import KNeighborsRegressor
from server.models.base_trainer import BaseTrainer

class KNNModel(BaseTrainer):
    def __init__(self, model_name: str, n_neighbors: int = 5, weights: str = "uniform", **kwargs):
        model = KNeighborsRegressor(n_neighbors=n_neighbors, weights=weights)
        super().__init__(model_name, model=model, **kwargs)
