"""
Main App - Authentication in header
"""
import streamlit as st
from tabs import train_tab, predict_tab, admin_tab
from config import build_urls, DEFAULT_API_BASE_URL
from auth import _restore_from_storage, _init_session_state, is_admin, is_authenticated
from components.auth_header import render_auth_section

# Set page config (must be first Streamlit command)
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide"
)

# Initialize session state FIRST
_init_session_state()

# Restore authentication from file cache (no JavaScript needed)
# This is done automatically when is_authenticated() is called below
# The file cache persists across page refreshes on the server side

# Use default API URL
api_base_url = DEFAULT_API_BASE_URL
urls = build_urls(api_base_url)

# ============================================
# SIDEBAR - Authentication
# ============================================
render_auth_section(api_base_url)

# ============================================
# MAIN CONTENT AREA - Tabs for navigation
# ============================================
# Tabs in main content area
tab_names = ["🏋️ Train Model", "🔮 Predict"]
# Add admin tab if user is admin
if is_authenticated() and is_admin(api_base_url):
    tab_names.append("🔐 Admin Dashboard")

tabs = st.tabs(tab_names)

with tabs[0]:
    train_tab.show_train_tab(urls)

with tabs[1]:
    predict_tab.show_predict_tab(urls)

# Admin tab (only if user is admin)
if len(tabs) > 2:
    with tabs[2]:
        admin_tab.show_admin_tab(urls)
