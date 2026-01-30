from sklearn.ensemble import RandomForestRegressor
from server.models.base_trainer import BaseTrainer


class RandomForestModel(BaseTrainer):
    OPTIONAL_PARAMS = {
        "n_estimators": "int",
        "max_depth": "int",
        "min_samples_split": "int",
        "min_samples_leaf": "int",
    }

    def __init__(
        self,
        model_name: str = "random_forest",
        n_estimators: int = 100,
        max_depth: int = 0,  # 0 means None (no limit) - converted in __init__
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        **kwargs,
    ):
        max_depth_arg = None if max_depth <= 0 else max_depth
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth_arg,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
        )
        super().__init__(model_name, model=model, **kwargs)
