"""
Authentication helper functions for the Streamlit client.
"""
import streamlit as st
import requests
import json
import os
from pathlib import Path
from typing import Optional, Dict, Tuple

# Cache file for authentication token (persists across page refreshes)
CACHE_DIR = Path.home() / ".streamlit_auth_cache"
CACHE_FILE = CACHE_DIR / "auth_token.json"


def _init_session_state():
    """
    Initialize session state for authentication.
    This ensures auth_token and user_email keys exist.
    """
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "auth_restored" not in st.session_state:
        st.session_state.auth_restored = False


def _save_token_to_storage(token: str, email: str):
    """
    Save authentication token to session state and local file cache.
    The file cache persists across page refreshes (server-side, no JavaScript needed).
    """
    st.session_state.auth_token = token
    st.session_state.user_email = email
    
    # Save to local file cache (persists across refreshes on server side)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump({"auth_token": token, "user_email": email}, f)
    except Exception as e:
        # File cache is optional, don't fail if it doesn't work
        pass


def _restore_from_storage():
    """
    Restore authentication token from local file cache (server-side, no JavaScript needed).
    This is called once per session to restore authentication after a page refresh.
    The file cache persists across browser refreshes on the server side.
    """
    if not st.session_state.get("auth_restored", False):
        # Restore from local file cache (server-side, no JavaScript needed)
        # This file persists across page refreshes
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
    """
    Get authentication headers for API requests.
    
    Args:
        token: JWT token. If None, retrieves from session state.
    
    Returns:
        Dictionary with Authorization header, or empty dict if no token.
    """
    if token is None:
        token = st.session_state.get("auth_token")
    
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def is_authenticated() -> bool:
    """
    Check if user is authenticated.
    
    Returns:
        True if auth token exists in session state, False otherwise.
    """
    _init_session_state()
    
    # Try to restore from storage on first check
    if not st.session_state.auth_restored:
        _restore_from_storage()
    
    return st.session_state.auth_token is not None and st.session_state.auth_token != ""


def login(email: str, password: str, api_base_url: str) -> Tuple[bool, str]:
    """
    Attempt to login and store token in session state.
    
    Args:
        email: User email
        password: User password
        api_base_url: Base URL for the API
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        response = requests.post(
            f"{api_base_url}/user/login",
            json={"email": email, "pwd": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                _save_token_to_storage(token, email)
                return True, "Login successful!"
            return False, "No token received from server"
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Login failed: {error_detail}"
    except Exception as e:
        return False, f"Error during login: {str(e)}"


def register(email: str, password: str, api_base_url: str) -> Tuple[bool, str]:
    """
    Register a new user account.
    
    Args:
        email: User email
        password: User password
        api_base_url: Base URL for the API
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        response = requests.post(
            f"{api_base_url}/user/create",
            json={"email": email, "pwd": password}
        )
        
        if response.status_code == 200:
            return True, "Account created successfully! Please log in."
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Registration failed: {error_detail}"
    except Exception as e:
        return False, f"Error during registration: {str(e)}"


def logout():
    """
    Clear authentication token from session state and file cache.
    """
    _init_session_state()
    
    st.session_state.auth_token = None
    st.session_state.user_email = None
    st.session_state.auth_restored = False
    
    # Clear from local file cache
    try:
        if CACHE_FILE.exists():
            os.remove(CACHE_FILE)
    except Exception:
        pass


def reset_password(email: str, new_password: str, api_base_url: str) -> Tuple[bool, str]:
    """
    Reset a user's password.
    
    Args:
        email: User email
        new_password: New password
        api_base_url: Base URL for the API
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        response = requests.post(
            f"{api_base_url}/user/reset_password",
            json={"email": email, "new_password": new_password}
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get("message", "Password reset successfully!")
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Password reset failed: {error_detail}"
    except Exception as e:
        return False, f"Error during password reset: {str(e)}"


def get_user_tokens(api_base_url: str) -> Optional[int]:
    """
    Get current user's token count.
    
    Args:
        api_base_url: Base URL for the API
    
    Returns:
        Token count if successful, None otherwise.
    """
    if not is_authenticated():
        return None
    
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{api_base_url}/user/tokens",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("tokens")
        return None
    except Exception:
        return None


def is_admin(api_base_url: str) -> bool:
    """
    Check if the current user is an admin by attempting to access admin endpoint.
    
    Args:
        api_base_url: Base URL for the API
    
    Returns:
        True if user is admin, False otherwise.
    """
    if not is_authenticated():
        return False
    
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{api_base_url}/admin/users",
            headers=headers
        )
        return response.status_code == 200
    except Exception:
        return False

