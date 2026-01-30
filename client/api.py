import requests
from typing import Any, Dict, Optional


def get_models(urls: Dict[str, str]):
    return requests.get(urls["MODELS"])


def get_trained_models(urls: Dict[str, str], headers: Dict[str, str]):
    return requests.get(urls["TRAINED"], headers=headers)


def get_model_details(urls: Dict[str, str], model_name: str, headers: Dict[str, str]):
    return requests.get(f"{urls['MODEL_DETAILS']}/{model_name}", headers=headers)


def create_model(urls: Dict[str, str], headers: Dict[str, str], data: Dict[str, Any], files: Dict):
    return requests.post(urls["CREATE"], data=data, files=files, headers=headers)


def predict_model(urls: Dict[str, str], model_name: str, headers: Dict[str, str], payload: Dict[str, Any]):
    return requests.post(f"{urls['PREDICT']}/{model_name}", json=payload, headers=headers)


def delete_model(urls: Dict[str, str], model_name: str, headers: Dict[str, str]):
    return requests.delete(f"{urls['DELETE_MODEL']}/{model_name}", headers=headers)


def login(urls: Dict[str, str], email: str, password: str):
    return requests.post(urls["USER_LOGIN"], json={"email": email, "pwd": password})


def register(urls: Dict[str, str], email: str, password: str):
    return requests.post(urls["USER_CREATE"], json={"email": email, "pwd": password})


def reset_password(urls: Dict[str, str], email: str, new_password: str, headers: Optional[Dict[str, str]] = None):
    return requests.post(
        urls["USER_RESET_PASSWORD"],
        json={"email": email, "new_password": new_password},
        headers=headers or {}
    )


def get_user_tokens(urls: Dict[str, str], headers: Dict[str, str]):
    return requests.get(urls["USER_TOKENS"], headers=headers)


def is_admin(urls: Dict[str, str], headers: Dict[str, str]):
    return requests.get(urls["ADMIN_USERS"], headers=headers)


def admin_get_users(urls: Dict[str, str], headers: Dict[str, str], min_tokens: Optional[int] = None):
    params = {"min_tokens": min_tokens} if min_tokens and min_tokens > 0 else {}
    return requests.get(urls["ADMIN_USERS"], headers=headers, params=params)


def admin_add_tokens(urls: Dict[str, str], user_id: int, headers: Dict[str, str], email: str, credit_card: str, amount: int):
    return requests.post(
        f"{urls['ADMIN_ADD_TOKENS']}/{user_id}/tokens",
        headers=headers,
        json={"email": email, "credit_card": credit_card, "amount": amount}
    )


def admin_reset_password(urls: Dict[str, str], user_id: int, headers: Dict[str, str], email: str, new_password: str):
    return requests.post(
        f"{urls['ADMIN_RESET_PASSWORD']}/{user_id}/reset_password",
        headers=headers,
        json={"email": email, "new_password": new_password}
    )


def admin_delete_user(urls: Dict[str, str], user_id: int, headers: Dict[str, str]):
    return requests.delete(f"{urls['ADMIN_DELETE_USER']}/{user_id}", headers=headers)
