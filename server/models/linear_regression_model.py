import json
import os
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


# ------------------------------------------------
# Paths
# ------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # server/models

TRAIN_MODELS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "train_models"))
METRICS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "metrics"))

os.makedirs(TRAIN_MODELS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)


# -----------------------------
# 1️⃣ Preprocess dates
# -----------------------------
def preprocess_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if "date" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].map(lambda x: x.timestamp() if pd.notnull(x) else 0)
    return df


# -----------------------------
# 2️⃣ Train function
# -----------------------------
def train_linear_regression_model(
    csv_file: str,
    feature_cols: list,
    label_col: str,
    train_percentage: float,
    model_filename: str
):
    if not (0 < train_percentage < 1):
        raise ValueError("train_percentage must be between 0 and 1")

    if not feature_cols:
        raise ValueError("feature_cols cannot be empty")

    df = pd.read_csv(csv_file)
    if df.empty:
        raise ValueError("CSV file is empty")

    df = preprocess_dates(df)

    missing_features = [col for col in feature_cols if col not in df.columns]
    if missing_features:
        raise ValueError(f"Feature columns not found in CSV: {missing_features}")

    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not found in CSV")

    X = df[feature_cols]
    y = df[label_col]

    string_cols = X.select_dtypes(include=["object"]).columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(drop="first"), string_cols),
        ],
        remainder="passthrough",
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression()),
    ])

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

    # ---------- Save model ----------
    model_path = os.path.join(TRAIN_MODELS_DIR, model_filename)
    joblib.dump(pipeline, model_path)

    # ---------- Save metrics ----------
    metrics_path = os.path.join(
        METRICS_DIR,
        model_filename.replace(".pkl", "_metrics.json")
    )

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)

    print(f"Model saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")

    return metrics


# -----------------------------
# 3️⃣ Predict function
# -----------------------------
def predict(model_filename: str, features: dict) -> float:
    model_path = os.path.join(TRAIN_MODELS_DIR, model_filename)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if not features:
        raise ValueError("Features dictionary cannot be empty")

    pipeline = joblib.load(model_path)
    x_input = pd.DataFrame([features])

    return float(pipeline.predict(x_input)[0])
