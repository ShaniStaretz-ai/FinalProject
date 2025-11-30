import json

import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# -----------------------------
# 1️⃣ Preprocess dates
# -----------------------------
def preprocess_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if "date" in col:
            df[col] = pd.to_datetime(df[col], errors='coerce')
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
    df = pd.read_csv(csv_file)
    df = preprocess_dates(df)

    X = df[feature_cols]
    y = df[label_col]

    # Identify string and numeric columns
    string_cols = X.select_dtypes(include=['object']).columns.tolist()
    numeric_cols = X.select_dtypes(include=['int64','float64']).columns.tolist()

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(drop='first'), string_cols),
        ],
        remainder='passthrough'  # keep numeric columns as-is
    )

    # Full pipeline with model
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ])

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=train_percentage, random_state=42)

    # Fit pipeline
    pipeline.fit(X_train, y_train)

    # Predict & evaluate
    y_pred = pipeline.predict(X_test)
    metrics = {
        "r2_score": r2_score(y_test, y_pred),
        "mean_squared_error": mean_squared_error(y_test, y_pred),
        "mean_absolute_error": mean_absolute_error(y_test, y_pred)
    }
    joblib.dump(pipeline, model_filename)
    print(f"Model saved to: {model_filename}")

    joblib.dump(pipeline, model_filename)
    print(f"Model saved to: {model_filename}")
    # Save metrics
    metrics_filename = model_filename.replace(".pkl", "_metrics.json")
    with open(metrics_filename, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"Metrics saved to: {metrics_filename}")
    print("Metrics:", metrics)
    return metrics

# -----------------------------
# 3️⃣ Predict function
# -----------------------------
def predict(model_filename: str, features: dict) -> float:
    pipeline = joblib.load(model_filename)
    x_input = pd.DataFrame([features])
    pred = pipeline.predict(x_input)
    return float(pred[0])

# -----------------------------
# 4️⃣ Example usage
# -----------------------------
if __name__ == "__main__":
    csv_file = "../../employees.csv"
    feature_cols = ["age", "salary", "city", "hire_date"]  # city is string
    label_col = "bonus"

    # Train
    train_linear_regression_model(csv_file, feature_cols, label_col, 0.8, "linear_model.pkl")

    # Predict
    new_employee = {
        "age": 30,
        "salary": 50000,
        "city": "Chicago",
        "hire_date": 1583020800  # already numeric
    }
    print("Prediction:", predict("linear_model.pkl", new_employee))
