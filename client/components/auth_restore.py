"""
Custom Streamlit component to restore authentication from browser localStorage.
"""
import streamlit.components.v1 as components

def restore_auth_component():
    """
    Component that reads auth token from localStorage and makes it available.
    Returns a component that can be used to restore authentication.
    """
    html_code = """
    <script>
        // Read from localStorage and store in a way Streamlit can access
        (function() {
            if (typeof(Storage) !== "undefined") {
                const token = localStorage.getItem("auth_token");
                const email = localStorage.getItem("user_email");
                if (token && email) {
                    // Store in window for potential access
                    window.streamlitAuthToken = token;
                    window.streamlitUserEmail = email;
                    
                    // Try to communicate with Streamlit via query params
                    const url = new URL(window.location);
                    if (!url.searchParams.has("auth_restored")) {
                        url.searchParams.set("auth_token", encodeURIComponent(token));
                        url.searchParams.set("user_email", encodeURIComponent(email));
                        url.searchParams.set("auth_restored", "true");
                        window.history.replaceState({}, "", url);
                    }
                }
            }
        })();
    </script>
    <div style="display:none;"></div>
    """
    return components.html(html_code, height=0, key="auth_restore")

