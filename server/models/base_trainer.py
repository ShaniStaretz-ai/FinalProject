import os
import json
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

from server.config import TRAIN_MODELS_DIR, METRICS_DIR
from server.core_models.server_logger import get_logger

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
        """
        Preprocess date columns by converting them to Unix timestamps.
        Detects date columns by checking pandas dtype, not just column name.
        """
        # Only log if date columns are found
        date_cols = [col for col in df.columns 
                    if pd.api.types.is_datetime64_any_dtype(df[col]) or "date" in col.lower()]
        if date_cols:
            self.logger.info(f"Preprocessing {len(date_cols)} date column(s)")
        for col in df.columns:
            # Check if column is datetime type or contains 'date' in name
            if pd.api.types.is_datetime64_any_dtype(df[col]) or "date" in col.lower():
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[col] = df[col].map(lambda x: x.timestamp() if pd.notnull(x) else 0)
        return df

    def train(self, csv_file, feature_cols, label_col, train_percentage=0.8):
        self.logger.info(f"Training: {len(feature_cols)} features, {label_col} label")
        if not (0 < train_percentage < 1):
            raise ValueError("train_percentage must be between 0 and 1")

        # Accept either CSV file path or DataFrame
        if isinstance(csv_file, str):
            df = pd.read_csv(csv_file)
        else:
            df = csv_file  # already a DataFrame

        df = self.preprocess_dates(df)

        # Validate columns exist
        missing_features = [col for col in feature_cols if col not in df.columns]
        if missing_features:
            raise ValueError(f"Feature columns not found in data: {missing_features}")
        
        if label_col not in df.columns:
            raise ValueError(f"Label column '{label_col}' not found in data")

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

        self.logger.info(f"Saved: R²={metrics['r2_score']:.3f}, MSE={metrics['mean_squared_error']:.2f}")

        return metrics

    def predict(self, features: dict):
        """
        Predict using a trained model.
        
        Args:
            features: Dictionary of feature names to values
            
        Returns:
            float: Prediction value
            
        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If features dictionary is empty
        """
        if not features:
            raise ValueError("Features dictionary cannot be empty")
        
        # Sanitize model name to prevent path traversal
        safe_model_name = os.path.basename(self.model_name)
        if safe_model_name != self.model_name:
            raise ValueError(f"Invalid model name: {self.model_name}")
        
        model_path = os.path.join(self.train_dir, f"{safe_model_name}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        model = joblib.load(model_path)
        return float(model.predict(pd.DataFrame([features]))[0])
