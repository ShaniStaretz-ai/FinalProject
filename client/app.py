import streamlit as st
from tabs import train_tab, predict_tab
from config import build_urls, DEFAULT_API_BASE_URL

# Sidebar
st.sidebar.header("API Settings")

api_base_url = st.sidebar.text_input(
    "API Base URL",
    DEFAULT_API_BASE_URL,
    key="api_base_url"
)

urls = build_urls(api_base_url)

# Tabs
tabs = st.tabs(["Train Model", "Predict"])

with tabs[0]:
    train_tab.show_train_tab(urls)

with tabs[1]:
    predict_tab.show_predict_tab(urls)
