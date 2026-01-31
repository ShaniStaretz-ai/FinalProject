import logging
import os


def setup_logging(level: int = logging.INFO, format_string: str = None):
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-5s | %(name)-20s | %(message)s"
    date_format = "%H:%M:%S"
    log_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "logs")
    )
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    formatter = logging.Formatter(format_string, datefmt=date_format)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(level)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    if "." in name:
        short_name = name.split(".")[-1]
    elif "_" in name and len(name) > 20:
        parts = name.split("_")
        if len(parts) >= 2:
            short_name = f"model:{parts[0]}_{parts[1]}"
        else:
            short_name = name[:20]
    else:
        short_name = name[:20] if len(name) > 20 else name
    logger = logging.getLogger(short_name)
    logger.setLevel(logging.INFO)
    logger.propagate = True
    return logger
