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
    Save authentication token to session state, browser localStorage, and local file cache.
    This ensures tokens persist across page refreshes.
    """
    st.session_state.auth_token = token
    st.session_state.user_email = email
    
    # Save to local file cache (persists across refreshes)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump({"auth_token": token, "user_email": email}, f)
    except Exception as e:
        # File cache is optional, don't fail if it doesn't work
        pass
    
    # Save to browser localStorage via JavaScript
    # Escape the token and email for JavaScript
    safe_token = token.replace('"', '\\"').replace("'", "\\'")
    safe_email = email.replace('"', '\\"').replace("'", "\\'")
    
    js_code = f"""
    <script>
        if (typeof(Storage) !== "undefined") {{
            localStorage.setItem("auth_token", "{safe_token}");
            localStorage.setItem("user_email", "{safe_email}");
        }}
    </script>
    """
    st.components.v1.html(js_code, height=0)


def _restore_from_storage():
    """
    Restore authentication token from local file cache, query params, or browser localStorage.
    This is called once per session to restore authentication after a page refresh.
    """
    if not st.session_state.get("auth_restored", False):
        # First, try to restore from local file cache (fastest, no JavaScript needed)
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
        
        # Second, try to get token from query parameters (set by JavaScript on previous load)
        try:
            query_params = st.query_params
            if "auth_token" in query_params and "user_email" in query_params:
                token = query_params["auth_token"]
                email = query_params["user_email"]
                if token and email:
                    st.session_state.auth_token = token
                    st.session_state.user_email = email
                    # Save to file cache for next time
                    try:
                        CACHE_DIR.mkdir(parents=True, exist_ok=True)
                        with open(CACHE_FILE, 'w') as f:
                            json.dump({"auth_token": token, "user_email": email}, f)
                    except Exception:
                        pass
                    # Clear query params after restoring to avoid showing them in URL
                    new_params = {k: v for k, v in query_params.items() 
                                 if k not in ["auth_token", "user_email", "auth_restored"]}
                    st.query_params = new_params
                    st.session_state.auth_restored = True
                    return
        except Exception:
            pass
        
        # Third, if not restored, inject JavaScript to read from localStorage
        # and set query params for next rerun
        if st.session_state.auth_token is None:
            js_code = """
            <script>
                (function() {
                    if (typeof(Storage) !== "undefined") {
                        const token = localStorage.getItem("auth_token");
                        const email = localStorage.getItem("user_email");
                        if (token && email) {
                            const url = new URL(window.location);
                            if (!url.searchParams.has("auth_token")) {
                                url.searchParams.set("auth_token", encodeURIComponent(token));
                                url.searchParams.set("user_email", encodeURIComponent(email));
                                url.searchParams.set("auth_restored", "true");
                                window.history.replaceState({}, "", url);
                                window.location.reload();
                            }
                        }
                    }
                })();
            </script>
            """
            st.markdown(js_code, unsafe_allow_html=True)
        
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
    Clear authentication token from session state, browser localStorage, and file cache.
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
    
    # Clear from browser localStorage and sessionStorage
    js_code = """
    <script>
        if (typeof(Storage) !== "undefined") {
            localStorage.removeItem("auth_token");
            localStorage.removeItem("user_email");
            sessionStorage.removeItem("auth_restore_attempted");
        }
    </script>
    """
    st.components.v1.html(js_code, height=0)


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

