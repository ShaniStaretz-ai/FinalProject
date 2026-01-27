import streamlit as st
from tabs import train_tab, predict_tab
from config import build_urls, DEFAULT_API_BASE_URL
from auth import is_authenticated, login, register, logout, get_user_tokens, reset_password, _restore_from_storage, _init_session_state

# Initialize session state FIRST
_init_session_state()

# Try to restore from query params (set by JavaScript on reload)
restored = False
try:
    query_params = st.query_params
    if "auth_token" in query_params and "user_email" in query_params:
        token = query_params.get("auth_token")
        email = query_params.get("user_email")
        if token and email:
            st.session_state.auth_token = token
            st.session_state.user_email = email
            st.session_state.auth_restored = True
            restored = True
            # Clear query params from URL
            new_params = {k: v for k, v in query_params.items() 
                         if k not in ["auth_token", "user_email", "auth_restored"]}
            st.query_params = new_params
except Exception:
    pass

# If not restored and no token in session, inject JavaScript to restore
# This will only run on the first page load (when there are no query params)
if not restored and not st.session_state.get("auth_token"):
    # Only inject script if we don't have query params (first load after refresh)
    if "auth_token" not in st.query_params:
        # Inject script that runs immediately and sets query params, then reloads
        restore_js = """
        <script>
            // Run immediately, don't wait for DOM
            (function() {
                try {
                    if (typeof(Storage) !== "undefined") {
                        const token = localStorage.getItem("auth_token");
                        const email = localStorage.getItem("user_email");
                        if (token && email) {
                            const currentUrl = window.location.href;
                            const url = new URL(currentUrl);
                            // Only proceed if auth_token is not already in URL
                            if (!url.searchParams.has("auth_token")) {
                                url.searchParams.set("auth_token", encodeURIComponent(token));
                                url.searchParams.set("user_email", encodeURIComponent(email));
                                url.searchParams.set("auth_restored", "1");
                                // Update URL without reload first
                                window.history.replaceState({}, "", url.toString());
                                // Then reload to let Streamlit read the params
                                window.location.reload();
                            }
                        }
                    }
                } catch(e) {
                    console.error("Auth restore error:", e);
                }
            })();
        </script>
        """
        # Use markdown with unsafe_allow_html to inject early
        st.markdown(restore_js, unsafe_allow_html=True)

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

# Tabs
tabs = st.tabs(["Train Model", "Predict"])

with tabs[0]:
    train_tab.show_train_tab(urls)

with tabs[1]:
    predict_tab.show_predict_tab(urls)
