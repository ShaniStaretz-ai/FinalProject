import streamlit as st
from tabs import train_tab, predict_tab
from config import build_urls, DEFAULT_API_BASE_URL
from auth import is_authenticated, login, register, logout, get_user_tokens, reset_password, _restore_from_storage, _init_session_state

# Initialize and restore authentication FIRST, before any other code
_init_session_state()
if not st.session_state.get("auth_restored", False):
    _restore_from_storage()

# Sidebar
st.sidebar.header("API Settings")

api_base_url = st.sidebar.text_input(
    "API Base URL",
    DEFAULT_API_BASE_URL,
    key="api_base_url"
)

urls = build_urls(api_base_url)

# Authentication Section
st.sidebar.header("Authentication")

if is_authenticated():
    user_email = st.session_state.get("user_email", "Unknown")
    st.sidebar.success(f"Logged in as: {user_email}")
    
    # Show token count
    tokens = get_user_tokens(api_base_url)
    if tokens is not None:
        st.sidebar.info(f"Tokens: {tokens}")
    
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()
else:
    # Login/Register/Reset Password Tabs
    auth_tabs = st.sidebar.tabs(["Login", "Register", "Reset Password"])
    
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
            st.caption("Password must be at least 4 characters")
            reg_submit = st.form_submit_button("Register")
            
            if reg_submit:
                success, message = register(reg_email, reg_password, api_base_url)
                if success:
                    st.sidebar.success(message)
                else:
                    st.sidebar.error(message)
    
    with auth_tabs[2]:
        st.info("💡 **Reset your password if you're having trouble logging in.**")
        with st.form("reset_password_form"):
            reset_email = st.text_input("Email", key="reset_email")
            reset_new_password = st.text_input("New Password", type="password", key="reset_new_password")
            st.caption("Password must be at least 4 characters")
            reset_submit = st.form_submit_button("Reset Password")
            
            if reset_submit:
                if not reset_email:
                    st.sidebar.error("Please enter your email address")
                elif not reset_new_password or len(reset_new_password) < 4:
                    st.sidebar.error("Password must be at least 4 characters")
                else:
                    success, message = reset_password(reset_email, reset_new_password, api_base_url)
                    if success:
                        st.sidebar.success(message)
                        st.sidebar.info("You can now log in with your new password.")
                    else:
                        st.sidebar.error(message)

# Tabs
tabs = st.tabs(["Train Model", "Predict"])

with tabs[0]:
    train_tab.show_train_tab(urls)

with tabs[1]:
    predict_tab.show_predict_tab(urls)
