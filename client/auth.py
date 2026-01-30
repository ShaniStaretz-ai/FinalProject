import streamlit as st
import json
import os
from pathlib import Path
from typing import Optional, Dict, Tuple

from config import build_urls
from api import login as api_login, register as api_register, reset_password as api_reset_password
from api import get_user_tokens as api_get_user_tokens, is_admin as api_is_admin

CACHE_DIR = Path.home() / ".streamlit_auth_cache"
CACHE_FILE = CACHE_DIR / "auth_token.json"


def _init_session_state():
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "auth_restored" not in st.session_state:
        st.session_state.auth_restored = False


def _save_token_to_storage(token: str, email: str):
    st.session_state.auth_token = token
    st.session_state.user_email = email
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump({"auth_token": token, "user_email": email}, f)
    except Exception:
        pass


def _restore_from_storage():
    if not st.session_state.get("auth_restored", False):
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                    token = cache_data.get("auth_token")
                    email = cache_data.get("user_email")
                    if token and email:
                        st.session_state.auth_token = token
                        st.session_state.user_email = email
                        st.session_state.auth_restored = True
                        return
        except Exception:
            pass
        st.session_state.auth_restored = True


def get_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    if token is None:
        token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def is_authenticated() -> bool:
    _init_session_state()
    if not st.session_state.auth_restored:
        _restore_from_storage()
    return st.session_state.auth_token is not None and st.session_state.auth_token != ""


def login(email: str, password: str, api_base_url: str) -> Tuple[bool, str]:
    try:
        urls = build_urls(api_base_url)
        response = api_login(urls, email, password)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                _save_token_to_storage(token, email)
                return True, "Login successful!"
            return False, "No token received from server"
        error_detail = response.json().get("detail", response.text) if response.text else "Unknown error"
        return False, f"Login failed: {error_detail}"
    except Exception as e:
        return False, f"Error during login: {str(e)}"


def register(email: str, password: str, api_base_url: str) -> Tuple[bool, str]:
    try:
        urls = build_urls(api_base_url)
        response = api_register(urls, email, password)
        if response.status_code == 200:
            return True, "Account created successfully! Please log in."
        error_detail = response.json().get("detail", response.text) if response.text else "Unknown error"
        return False, f"Registration failed: {error_detail}"
    except Exception as e:
        return False, f"Error during registration: {str(e)}"


def logout():
    _init_session_state()
    st.session_state.auth_token = None
    st.session_state.user_email = None
    st.session_state.auth_restored = False
    try:
        if CACHE_FILE.exists():
            os.remove(CACHE_FILE)
    except Exception:
        pass


def logout_and_rerun():
    logout()
    st.rerun()


def reset_password(email: str, new_password: str, api_base_url: str) -> Tuple[bool, str]:
    if not is_authenticated():
        return False, "Please log in to reset your password."
    try:
        urls = build_urls(api_base_url)
        headers = get_auth_headers()
        response = api_reset_password(urls, email, new_password, headers)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("message", "Password reset successfully!")
        if response.status_code == 401:
            logout_and_rerun()
            return False, "Session expired. Please log in again."
        error_detail = response.json().get("detail", response.text) if response.text else "Unknown error"
        return False, f"Password reset failed: {error_detail}"
    except Exception as e:
        return False, f"Error during password reset: {str(e)}"


def get_user_tokens(api_base_url: str) -> Optional[int]:
    if not is_authenticated():
        return None
    try:
        urls = build_urls(api_base_url)
        headers = get_auth_headers()
        response = api_get_user_tokens(urls, headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("tokens")
        if response.status_code == 401:
            logout_and_rerun()
        return None
    except Exception:
        return None


def is_admin(api_base_url: str) -> bool:
    if not is_authenticated():
        return False
    try:
        urls = build_urls(api_base_url)
        headers = get_auth_headers()
        response = api_is_admin(urls, headers)
        if response.status_code == 401:
            logout_and_rerun()
        return response.status_code == 200
    except Exception:
        return False
