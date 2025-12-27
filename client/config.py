import streamlit as st
# --- Sidebar: API URL ---
st.sidebar.header("API Settings")
# Allow user to override via sidebar input
API_BASE_URL = st.sidebar.text_input("API Base URL", "http://127.0.0.1:8000")

# Derived URLs
API_CREATE_URL = f"{API_BASE_URL}/create"
API_PREDICT_URL = f"{API_BASE_URL}/predict"
API_MODELS_URL = f"{API_BASE_URL}/models"