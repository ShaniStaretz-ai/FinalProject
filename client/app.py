import streamlit as st
from tabs import train_tab, predict_tab, admin_tab
from config import build_urls, DEFAULT_API_BASE_URL
from auth import _restore_from_storage, _init_session_state, is_admin, is_authenticated
from components.auth_header import render_auth_section

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")
_init_session_state()

api_base_url = DEFAULT_API_BASE_URL
urls = build_urls(api_base_url)
render_auth_section(api_base_url)

tab_names = ["🏋️ Train Model", "🔮 Predict"]
if is_authenticated() and is_admin(api_base_url):
    tab_names.append("🔐 Admin Dashboard")

tabs = st.tabs(tab_names)
with tabs[0]:
    train_tab.show_train_tab(urls)
with tabs[1]:
    predict_tab.show_predict_tab(urls)
if len(tabs) > 2:
    with tabs[2]:
        admin_tab.show_admin_tab(urls, api_base_url)
