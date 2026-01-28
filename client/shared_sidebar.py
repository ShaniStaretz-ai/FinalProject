"""
Shared sidebar component for all pages.
"""
import streamlit as st
from config import build_urls, DEFAULT_API_BASE_URL
from auth import is_authenticated, login, register, logout, get_user_tokens, reset_password, is_admin

def render_sidebar():
    """Render the shared sidebar with auth and settings."""
    # Use default API URL (no user input needed)
    api_base_url = DEFAULT_API_BASE_URL
    urls = build_urls(api_base_url)
    
    # Authentication Section (appears right after pages menu)
    st.sidebar.header("🔐 Authentication")

    # Note about page refresh behavior
    if not is_authenticated() and st.session_state.get("show_refresh_note", True):
        with st.sidebar.expander("ℹ️ About Page Refresh", expanded=False):
            st.info("""
            **Note:** Full page refreshes (F5) will log you out due to Streamlit's architecture.
            
            To stay logged in:
            - Use Streamlit's built-in rerun (interact with widgets)
            - Avoid pressing F5 or refreshing the browser
            - Your login is saved in browser storage and will auto-restore when possible
            """)
            if st.button("Don't show again", key="hide_refresh_note"):
                st.session_state.show_refresh_note = False
                st.rerun()

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
    
    return urls, api_base_url
