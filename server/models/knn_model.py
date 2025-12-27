from sklearn.neighbors import KNeighborsRegressor
from server.models.base_trainer import BaseTrainer


class KNNModel(BaseTrainer):
    def __init__(self, n_neighbors=5, weights="distance"):
        super().__init__(
            model=KNeighborsRegressor(
                n_neighbors=n_neighbors,
                weights=weights
            ),
            model_name="knn"
        )

if __name__ == "__main__":
    model = KNNModel(
        n_neighbors=5,
        weights="distance"
    )

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

    print("Metrics:", metrics)
    print("Prediction:", prediction)