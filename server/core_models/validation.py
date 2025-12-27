import os

def validate_create_body(body: dict):
    """
    Validate input for /create endpoint
    """
    required_fields = ["csv_file", "feature_cols", "label_col", "train_percentage", "model_filename"]
    missing = [k for k in required_fields if k not in body]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")

    if not os.path.exists(body["csv_file"]):
        raise ValueError(f"CSV file not found: {body['csv_file']}")

    if not (0 < body["train_percentage"] < 1):
        raise ValueError("train_percentage must be between 0 and 1")

    if not isinstance(body["feature_cols"], list) or not all(isinstance(f, str) for f in body["feature_cols"]):
        raise ValueError("feature_cols must be a list of strings")

    if not isinstance(body["label_col"], str):
        raise ValueError("label_col must be a string")

    filename = body["model_filename"]
    if not isinstance(filename, str) or not filename or any(x in filename for x in ("/", "\\", "..")):
        raise ValueError("Invalid model filename")


def validate_predict_body(body: dict):
    """
    Validate input for /predict endpoint
    """
    if "features" not in body or not isinstance(body["features"], dict):
        raise ValueError("'features' is required and must be a dictionary")
