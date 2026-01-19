import os
from psycopg2 import connect
from dotenv import load_dotenv
from pathlib import Path


_REQUIRED_VARS = [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
]


def _load_env():
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path)


def _validate_env():
    missing = [v for v in _REQUIRED_VARS if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {missing}")


def get_connection():
    _load_env()
    _validate_env()

    return connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
