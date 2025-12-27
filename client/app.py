import streamlit as st
from tabs import train_tab, predict_tab
from config import API_CREATE_URL, API_PREDICT_URL, API_MODELS_URL




# --- Tabs ---
tabs = st.tabs(["Train Model", "Predict"])

############################
# --- Tab 1: Train Model ---
############################
with tabs[0]:
    train_tab.show_train_tab(API_CREATE_URL,API_MODELS_URL)
############################
# --- Tab 2: Predict ---
############################
with tabs[1]:
    predict_tab.show_predict_tab(API_PREDICT_URL)