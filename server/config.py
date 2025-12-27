import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRAIN_MODELS_DIR = os.path.join(BASE_DIR, "train_models")
METRICS_DIR = os.path.join(BASE_DIR, "metrics")

os.makedirs(TRAIN_MODELS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)
