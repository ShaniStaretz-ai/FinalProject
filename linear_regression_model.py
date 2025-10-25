import json
import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split

# -----------------------------
# 1️⃣ Training function
# -----------------------------
def train_linear_regression_model(
    csv_file: str,
    feature_cols: list,
    label_col: str,
    train_percentage: float,
    model_filename: str,
    col_types: dict,
    metrics_filename: str = None
):
    """
    Trains a Linear Regression model, encodes categorical columns, converts dates to timestamps,
    saves the model and metrics.
    """
    df = pd.read_csv(csv_file)

    # Convert date columns to timestamps
    for col, col_type in col_types.items():
        if col_type == "date" and col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[col] = df[col].map(lambda x: x.timestamp() if pd.notnull(x) else 0)

    # One-hot encode string columns
    string_cols = [col for col, t in col_types.items() if t == "string" and col in df.columns]
    df = pd.get_dummies(df, columns=string_cols, drop_first=True)

    # Determine valid features after encoding
    valid_features = []
    for feat in feature_cols:
        if feat in df.columns:
            valid_features.append(feat)
        else:
            # Include dummy columns
            valid_features.extend([c for c in df.columns if c.startswith(f"{feat}_")])

    if not valid_features:
        raise ValueError("No valid feature columns found after encoding")

    x = df[valid_features]
    y = df[label_col]

    # Train/test split
    x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=train_percentage, random_state=42)

    # Train model
    model = LinearRegression()
    model.fit(x_train, y_train)

    # Evaluate
    y_pred = model.predict(x_test)
    metrics = {
        "r2_score": r2_score(y_test, y_pred),
        "mean_squared_error": mean_squared_error(y_test, y_pred),
        "mean_absolute_error": mean_absolute_error(y_test, y_pred)
    }

    # Save model
    joblib.dump(model, model_filename)

    # Save metrics
    if metrics_filename is None:
        metrics_filename = model_filename.replace(".pkl", "_metrics.json")
    with open(metrics_filename, "w") as f:
        json.dump(metrics, f, indent=4)

    # Save trained columns for prediction later
    trained_columns_filename = model_filename.replace(".pkl", "_columns.json")
    with open(trained_columns_filename, "w") as f:
        json.dump(valid_features, f)

    print(f"Model saved to: {model_filename}")
    print(f"Metrics saved to: {metrics_filename}")
    print(f"Trained columns saved to: {trained_columns_filename}")
    print("Metrics:", metrics)

    return metrics

# -----------------------------
# 2️⃣ Input preparation function
# -----------------------------
def prepare_input(features: dict, trained_columns: list, col_types: dict) -> pd.DataFrame:
    """
    Prepares a single input dict for prediction: converts dates, encodes strings, aligns columns.
    """
    x_input = pd.DataFrame([features])

    # Convert date columns to timestamps
    for col, col_type in col_types.items():
        if col_type == "date" and col in x_input.columns:
            x_input[col] = pd.to_datetime(x_input[col], errors='coerce')
            x_input[col] = x_input[col].map(lambda x: x.timestamp() if pd.notnull(x) else 0)

    # One-hot encode string columns
    string_cols = [col for col, t in col_types.items() if t == "string" and col in x_input.columns]
    x_input = pd.get_dummies(x_input, columns=string_cols, drop_first=True)

    # Add missing columns and ensure order
    x_input = x_input.reindex(columns=trained_columns, fill_value=0)

    return x_input

# -----------------------------
# 3️⃣ Prediction function
# -----------------------------
def predict(model_filename: str, features: dict, col_types: dict) -> float:
    """
    Loads model and trained columns, prepares input, and returns prediction.
    """
    # Load model
    model = joblib.load(model_filename)

    # Load trained columns
    trained_columns_filename = model_filename.replace(".pkl", "_columns.json")
    with open(trained_columns_filename, "r") as f:
        trained_columns = json.load(f)

    # Prepare input
    x_input = prepare_input(features, trained_columns, col_types)

    # Predict
    prediction = model.predict(x_input)
    return float(prediction[0])

# -----------------------------
# 4️⃣ Example usage
# -----------------------------
if __name__ == "__main__":
    _csv_file = "employees.csv"
    _feature_cols = ["age", "salary", "city", "hire_date"]
    _label_col = "bonus"
    _col_types = {"age": "numeric", "salary": "numeric", "city": "string", "hire_date": "date"}

    # Train
    train_linear_regression_model(_csv_file, _feature_cols, _label_col, 0.8, "linear.pkl", _col_types)

    # Predict
    features = {"age": 30, "salary": 50000, "city": "Chicago", "hire_date": 1583020800}
    pred = predict("linear.pkl", features, _col_types)
    print("Prediction:", pred)
