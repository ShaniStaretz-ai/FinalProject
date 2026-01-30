from sklearn.linear_model import LogisticRegression
from server.ml.base_trainer import BaseTrainer


class LogisticModel(BaseTrainer):
    OPTIONAL_PARAMS = {
        "C": "float",
        "max_iter": "int",
        "solver": "str",
    }

    def __init__(
        self,
        model_name: str = "logistic",
        C: float = 1.0,
        max_iter: int = 100,
        solver: str = "lbfgs",
        **kwargs,
    ):
        model = LogisticRegression(C=C, max_iter=max_iter, solver=solver)
        super().__init__(model_name, model=model, **kwargs)
