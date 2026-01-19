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
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_string
    )


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    Prevents duplicate handlers.
    """

    log_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "logs")
    )
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "app.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

