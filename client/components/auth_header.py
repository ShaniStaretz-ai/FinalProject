import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import is_authenticated, login, register, logout, get_user_tokens, reset_password
from config import DEFAULT_API_BASE_URL


def render_auth_section(api_base_url: str = DEFAULT_API_BASE_URL):
    st.sidebar.markdown("---")
    st.sidebar.header("🔐 Authentication")
    if is_authenticated():
        user_email = st.session_state.get("user_email", "Unknown")
        st.sidebar.success(f"**{user_email}**")
        tokens = get_user_tokens(api_base_url)
        if tokens is not None:
            st.sidebar.info(f"💰 Tokens: {tokens}")
        with st.sidebar.expander("Reset password"):
            with st.form("reset_password_form"):
                st.caption(f"Resetting password for {user_email}")
                reset_new_password = st.text_input("New Password", type="password", key="reset_new_password")
                st.caption("Min 4 characters")
                reset_submit = st.form_submit_button("Reset")
                if reset_submit:
                    if not reset_new_password or len(reset_new_password) < 4:
                        st.sidebar.error("Password must be at least 4 characters")
                    else:
                        success, message = reset_password(user_email, reset_new_password, api_base_url)
                        if success:
                            st.sidebar.success(message)
                        else:
                            st.sidebar.error(message)
        if st.sidebar.button("Logout", key="logout_btn", type="primary"):
            logout()
            st.rerun()
    else:
        auth_tabs = st.sidebar.tabs(["Login", "Register"])
        with auth_tabs[0]:
            with st.form("login_form"):
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                login_submit = st.form_submit_button("Login")
                if login_submit:
                    success, message = login(login_email, login_password, api_base_url)
                    if success:
                        st.sidebar.success(message)
                        st.rerun()
                    else:
                        st.sidebar.error(message)
        with auth_tabs[1]:
            with st.form("register_form"):
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                st.caption("Min 4 characters")
                reg_submit = st.form_submit_button("Register")
                if reg_submit:
                    success, message = register(reg_email, reg_password, api_base_url)
                    if success:
                        st.sidebar.success(message)
                    else:
                        st.sidebar.error(message)
        st.sidebar.caption("Log in to reset your password.")
