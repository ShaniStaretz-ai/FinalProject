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

    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())
    columns = df.columns.tolist()

    # -----------------------------
    # Feature & Label
    # -----------------------------
    feature_cols = st.multiselect("Select feature columns", columns)
    label_col_options = [c for c in columns if c not in feature_cols]
    if not label_col_options:
        st.error("Please deselect some feature columns to have at least one label column.")
        return
    label_col = st.selectbox("Select label column", label_col_options)
    train_percentage = st.slider("Training %", 0.5, 0.95, 0.8, 0.05)

    # -----------------------------
    # Model Type & Optional Params
    # -----------------------------
    try:
        model_types_data = requests.get(API_MODELS_URL).json()
    except Exception:
        model_types_data = {}

    if not model_types_data:
        # Fallback
        model_types_data = {"linear": {"params": {}}}

    model_type = st.selectbox("Select model type", list(model_types_data.keys()))
    st.subheader("Optional Parameters")

    optional_params = {}
    # Fallback: basic types
    default_model_params = {
        "linear": {"fit_intercept": {"type": "bool"}},
        "knn": {
            "n_neighbors": {"type": "int"},
            "weights": {"type": "select", "options": ["uniform", "distance"]}
        }
    }

    params_config = default_model_params.get(model_type, {})

    for param, param_config in params_config.items():
        param_type = param_config.get("type", "str")

        match param_type:
            case "int":
                optional_params[param] = st.number_input(param, value=5)
            case "float":
                optional_params[param] = st.number_input(param, value=0.8)
            case "bool":
                optional_params[param] = st.checkbox(param, value=True)
            case "str":
                optional_params[param] = st.text_input(param)
            case "select":
                options = param_config.get("options", [])
                optional_params[param] = st.selectbox(param, options)
            case _:
                st.warning(f"Unknown parameter type '{param_type}' for {param}")

    # -----------------------------
    # Train
    # -----------------------------
    if st.button("Train Model"):
        if not feature_cols or not label_col:
            st.error("Please select feature and label columns.")
        else:
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