"""
Helper functions for model routes.
"""
import json
import logging
from typing import Any, Dict

import pandas as pd
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)


def parse_csv(upload_file: UploadFile) -> pd.DataFrame:
    """
    Reads an uploaded CSV file and returns a pandas DataFrame.
    Raises HTTPException on errors.
    Enforces a maximum file size limit of 50MB to prevent DoS attacks.
    """
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    try:
        contents = upload_file.file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Check file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"CSV file too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )
        
        # Reset pointer in case file is read again
        upload_file.file.seek(0)
        df = pd.read_csv(upload_file.file)
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file has no data")
        return df
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        logger.exception("Failed to read CSV")
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {e}")


def parse_json_param(param: str, param_name: str) -> Any:
    """
    Parses a JSON string parameter and raises HTTPException if invalid.
    For 'feature_cols', also accepts comma-separated string format as fallback.
    """
    try:
        return json.loads(param)
    except json.JSONDecodeError:
        # Special handling for feature_cols: accept comma-separated string
        if param_name == "feature_cols":
            # Try to parse as comma-separated string
            if isinstance(param, str) and not param.startswith('['):
                # Split by comma and strip whitespace
                return [col.strip() for col in param.split(',') if col.strip()]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON in parameter '{param_name}'. Expected JSON format (e.g., [\"age\",\"salary\"] for feature_cols)"
        )


def convert_parameter_type(value: Any, expected_type: str) -> Any:
    """
    Convert a parameter value to the expected type using a switch-case pattern.
    
    Args:
        value: The value to convert
        expected_type: The target type as a string ("int", "bool", "float", "str")
    
    Returns:
        The converted value
    
    Raises:
        ValueError: If conversion fails
        TypeError: If conversion fails due to incompatible type
    """
    # Switch-case pattern using dictionary mapping
    type_converters = {
        "int": lambda v: int(v),
        "bool": lambda v: (
            v.lower() in ("true", "1", "yes") if isinstance(v, str)
            else bool(v)
        ),
        "float": lambda v: float(v),
        "str": lambda v: str(v),
    }
    
    # Get the converter function for the expected type
    converter = type_converters.get(expected_type)
    
    if converter is None:
        # Default to string conversion for unknown types
        return str(value)
    
    # Execute the conversion
    return converter(value)


def validate_optional_params(trainer_cls, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filters and converts the optional parameters to include only valid keys defined in trainer_cls.OPTIONAL_PARAMS.
    Performs type conversion based on the expected type.
    """
    allowed_params = getattr(trainer_cls, "OPTIONAL_PARAMS", {})
    invalid_keys = [k for k in params.keys() if k not in allowed_params]
    if invalid_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid optional parameter(s): {invalid_keys}"
        )
    
    # Convert and filter parameters
    converted_params = {}
    for key in params:
        if key in allowed_params:
            expected_type = allowed_params[key]
            value = params[key]
            
            # Type conversion using the separate function
            try:
                converted_params[key] = convert_parameter_type(value, expected_type)
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid type for parameter '{key}': expected {expected_type}, got {type(value).__name__}. Error: {str(e)}"
                )
    
    return converted_params

