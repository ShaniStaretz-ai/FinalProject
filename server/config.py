import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = Path(BASE_DIR) / ".env"
load_dotenv(env_path)

# Server directory (where this config file is located)
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))

TRAIN_MODELS_DIR = os.path.join(SERVER_DIR, "train_models")
METRICS_DIR = os.path.join(SERVER_DIR, "metrics") #TODO: save metric in the db instead

os.makedirs(TRAIN_MODELS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)

# JWT Configuration - JWT_SECRET is required for security
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is required for security. "
        "Please set it in your .env file in the project root. "
        "Example: JWT_SECRET=your-secret-key-here"
    )
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))