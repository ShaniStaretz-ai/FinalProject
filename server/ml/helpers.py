import json
import logging
from typing import Any, Dict
import pandas as pd
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024


def parse_csv(upload_file: UploadFile) -> pd.DataFrame:
    try:
        contents = upload_file.file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"CSV file too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )
        upload_file.file.seek(0)
        df = pd.read_csv(upload_file.file)
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file has no data")
        return df
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to read CSV")
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {e}")


def parse_json_param(param: str, param_name: str) -> Any:
    try:
        return json.loads(param)
    except json.JSONDecodeError:
        if param_name == "feature_cols":
            if isinstance(param, str) and not param.startswith('['):
                return [col.strip() for col in param.split(',') if col.strip()]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON in parameter '{param_name}'. Expected JSON format (e.g., [\"age\",\"salary\"] for feature_cols)"
        )


def convert_parameter_type(value: Any, expected_type: Any) -> Any:
    if isinstance(expected_type, dict):
        expected_type = expected_type.get("type", "str")
    type_converters = {
        "int": lambda v: int(v),
        "bool": lambda v: (
            v.lower() in ("true", "1", "yes") if isinstance(v, str)
            else bool(v)
        ),
        "float": lambda v: float(v),
        "str": lambda v: str(v),
    }
    converter = type_converters.get(expected_type)
    if converter is None:
        return str(value)
    return converter(value)


def validate_optional_params(trainer_cls, params: Dict[str, Any]) -> Dict[str, Any]:
    allowed_params = getattr(trainer_cls, "OPTIONAL_PARAMS", {})
    invalid_keys = [k for k in params.keys() if k not in allowed_params]
    if invalid_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid optional parameter(s): {invalid_keys}"
        )
    converted_params = {}
    for key in params:
        if key in allowed_params:
            expected_type = allowed_params[key]
            value = params[key]
            try:
                converted_params[key] = convert_parameter_type(value, expected_type)
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid type for parameter '{key}': expected {expected_type}, got {type(value).__name__}. Error: {str(e)}"
                )
    return converted_params
