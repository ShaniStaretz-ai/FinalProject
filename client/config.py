# config.py

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"

def build_urls(base_url: str):
    return {
        "CREATE": f"{base_url}/create",
        "PREDICT": f"{base_url}/predict",
        "MODELS": f"{base_url}/models",
    }
