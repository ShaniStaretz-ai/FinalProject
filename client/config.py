import os

DEFAULT_API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


def build_urls(base_url: str):
    return {
        "CREATE": f"{base_url}/create",
        "PREDICT": f"{base_url}/predict",
        "MODELS": f"{base_url}/models",
        "TRAINED": f"{base_url}/trained",
        "MODEL_DETAILS": f"{base_url}/trained",
        "DELETE_MODEL": f"{base_url}/delete",
        "USER_CREATE": f"{base_url}/user/create",
        "USER_LOGIN": f"{base_url}/user/login",
        "USER_TOKENS": f"{base_url}/user/tokens",
        "USER_RESET_PASSWORD": f"{base_url}/user/reset_password",
        "ADMIN_USERS": f"{base_url}/admin/users",
        "ADMIN_ADD_TOKENS": f"{base_url}/admin/users",
        "ADMIN_DELETE_USER": f"{base_url}/admin/users",
        "ADMIN_RESET_PASSWORD": f"{base_url}/admin/users",
    }
