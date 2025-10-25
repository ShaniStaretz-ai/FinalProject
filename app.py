import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from tabs import train_tab, predict_tab

# --- Sidebar: API URL ---
st.sidebar.header("API Settings")
API_BASE_URL = st.sidebar.text_input("API Base URL", "http://127.0.0.1:8000")
CREATE_URL = f"{API_BASE_URL}/create"
PREDICT_URL = f"{API_BASE_URL}/predict"

# --- Tabs ---
tabs = st.tabs(["Train Model", "Predict"])

############################
# --- Tab 1: Train Model ---
############################
with tabs[0]:
    train_tab.show_train_tab(CREATE_URL)
############################
# --- Tab 2: Predict ---
############################
with tabs[1]:
    predict_tab.show_predict_tab(PREDICT_URL)