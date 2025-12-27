import streamlit as st
import requests
import json
import pandas as pd

def show_train_tab(urls):
    API_CREATE_URL = urls["CREATE"]
    API_MODELS_URL = urls["MODELS"]

    st.header("Train Model")

    # -----------------------------
    # Upload CSV
    # -----------------------------
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if not uploaded_file:
        st.info("Please upload a CSV file to continue.")
        return

    # Rewind before reading
    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())
    columns = df.columns.tolist()

    # -----------------------------
    # Feature & Label Selection
    # -----------------------------
    feature_cols = st.multiselect("Select feature columns", options=columns)
    remaining_cols = [c for c in columns if c not in feature_cols]
    label_col = st.selectbox("Select label column", options=remaining_cols)
    train_percentage = st.slider("Training %", 0.5, 0.95, 0.8, 0.05)

    # -----------------------------
    # Model Type & Optional Params
    # -----------------------------
    try:
        model_types_resp = requests.get(API_MODELS_URL).json()
    except Exception:
        model_types_resp = {}

    if not model_types_resp:
        model_types_resp = {"linear": {"params": {}}}  # default fallback

    model_type = st.selectbox("Select model type", options=list(model_types_resp.keys()))

    st.subheader("Optional Parameters")
    optional_params = {}
    for param_name, param_type in model_types_resp.get(model_type, {}).get("params", {}).items():
        if param_type == "int":
            optional_params[param_name] = st.number_input(param_name, value=0, step=1)
        elif param_type == "float":
            optional_params[param_name] = st.number_input(param_name, value=0.0)
        elif param_type == "str":
            optional_params[param_name] = st.text_input(param_name)
        elif isinstance(param_type, dict) and param_type.get("type") == "select":
            optional_params[param_name] = st.selectbox(param_name, options=param_type.get("options", []))

    # -----------------------------
    # Train Model Button
    # -----------------------------
    if st.button("Train Model"):
        if not feature_cols or not label_col:
            st.error("Please select feature and label columns.")
            return

        # Rewind uploaded_file before sending
        uploaded_file.seek(0)
        files = {"csv_file": (uploaded_file.name, uploaded_file, "text/csv")}
        data = {
            "model_type": model_type,
            "feature_cols": json.dumps(feature_cols),
            "label_col": label_col,
            "train_percentage": train_percentage,
            "optional_params": json.dumps(optional_params)
        }

        with st.spinner("Training model..."):
            response = requests.post(API_CREATE_URL, data=data, files=files)

        if response.ok:
            st.success("Model training started successfully!")
            st.json(response.json())
        else:
            st.error(f"Training failed: {response.text}")
