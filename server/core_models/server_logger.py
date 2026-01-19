import logging
import os


def setup_logging(level: int = logging.INFO, format_string: str = None):
    """
    Set up basic logging configuration for the application.
    Should be called early in the application startup.
    
    Args:
        level: Logging level (default: logging.INFO)
        format_string: Custom format string for log messages
    """
    # More concise format: HH:MM:SS | LEVEL | Module | Message
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-5s | %(name)-20s | %(message)s"
    
    # Use shorter time format (HH:MM:SS instead of full datetime)
    date_format = "%H:%M:%S"
    
    log_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "logs")
    )
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    
    # Create formatter
    formatter = logging.Formatter(format_string, datefmt=date_format)
    
    # Configure root logger - only if not already configured
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(level)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        # Update existing handlers with new format
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    Uses root logger configuration to prevent duplicate handlers.
    """
    # Extract short module name from full path
    # e.g., "server.models.base_trainer" -> "base_trainer"
    # or "3_knn_20260119_185844_559891" -> "model:3_knn"
    if "." in name:
        short_name = name.split(".")[-1]
    elif "_" in name and len(name) > 20:
        # For model names like "3_knn_20260119_185844_559891", use shorter version
        parts = name.split("_")
        if len(parts) >= 2:
            short_name = f"model:{parts[0]}_{parts[1]}"
        else:
            short_name = name[:20]
    else:
        short_name = name[:20] if len(name) > 20 else name
    
    logger = logging.getLogger(short_name)
    logger.setLevel(logging.INFO)
    
    # Don't add handlers - use root logger's handlers to prevent duplication
    logger.propagate = True
    
    return logger

