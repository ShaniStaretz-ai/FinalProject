import os
import json
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

from server.config import TRAIN_MODELS_DIR, METRICS_DIR
from server.core_models.logger import get_logger

class BaseTrainer:
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.model = kwargs.get("model", None)
        self.logger = get_logger(self.model_name)

        self.train_dir = TRAIN_MODELS_DIR
        self.metrics_dir = METRICS_DIR
        os.makedirs(self.train_dir, exist_ok=True)
        os.makedirs(self.metrics_dir, exist_ok=True)

    def preprocess_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Preprocessing date columns")
        for col in df.columns:
            if "date" in col:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[col] = df[col].map(lambda x: x.timestamp() if pd.notnull(x) else 0)
        return df

    def train(self, csv_file, feature_cols, label_col, train_percentage=0.8):
        self.logger.info("Starting training process")
        if not (0 < train_percentage < 1):
            raise ValueError("train_percentage must be between 0 and 1")

            # Accept either CSV file path or DataFrame
        if isinstance(csv_file, str):
            df = pd.read_csv(csv_file)
        else:
            df = csv_file  # already a DataFrame

        df = self.preprocess_dates(df)

        X = df[feature_cols]
        y = df[label_col]

        string_cols = X.select_dtypes(include=["object"]).columns.tolist()

        preprocessor = ColumnTransformer(
            transformers=[("cat", OneHotEncoder(drop="first"), string_cols)],
            remainder="passthrough",
        )

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", self.model)
        ])

        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, train_size=train_percentage, random_state=42
        )

        self.logger.info("Training model...")
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        metrics = {
            "r2_score": r2_score(y_test, y_pred),
            "mean_squared_error": mean_squared_error(y_test, y_pred),
            "mean_absolute_error": mean_absolute_error(y_test, y_pred),
        }

        model_path = os.path.join(self.train_dir, f"{self.model_name}.pkl")
        metrics_path = os.path.join(self.metrics_dir, f"{self.model_name}_metrics.json")

        joblib.dump(pipeline, model_path)
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=4)

        self.logger.info(f"Model saved: {model_path}")
        self.logger.info(f"Metrics saved: {metrics_path}")

        return metrics

    def predict(self, features: dict):
        model_path = os.path.join(self.train_dir, f"{self.model_name}.pkl")
        self.logger.info("Loading model for prediction")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        model = joblib.load(model_path)
        return float(model.predict(pd.DataFrame([features]))[0])
