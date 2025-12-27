from sklearn.linear_model import LinearRegression
from server.models.base_trainer import BaseTrainer

class LinearRegressionModel(BaseTrainer):
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, model=LinearRegression(), **kwargs)


if __name__ == "__main__":
    model = LinearRegressionModel("LinearRegression")

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