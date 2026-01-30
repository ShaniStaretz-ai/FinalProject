import streamlit as st
import requests
import json
import pandas as pd
from auth import is_authenticated, get_auth_headers, logout_and_rerun

def show_train_tab(urls):
    API_CREATE_URL = urls["CREATE"]
    API_MODELS_URL = urls["MODELS"]

    st.header("Train Model")

    # Check authentication
    if not is_authenticated():
        st.warning("⚠️ Please log in to train models.")
        return

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
    # Fallback: basic types (when API not available)
    default_model_params = {
        "linear": {"fit_intercept": {"type": "bool"}},
        "knn": {
            "n_neighbors": {"type": "int"},
            "weights": {"type": "select", "options": ["uniform", "distance"]}
        },
        "logistic": {
            "C": {"type": "float", "label": "C (inverse of regularization strength; smaller = stronger regularization)", "value": 1.0},
            "max_iter": {"type": "int", "label": "max_iter (maximum number of iterations for the solver to converge)", "value": 100},
            "solver": {"type": "str", "label": "solver (algorithm: lbfgs, liblinear, newton-cg, sag, or saga)", "value": "lbfgs"},
        },
        "random_forest": {
            "n_estimators": {"type": "int"},
            "max_depth": {"type": "int"},
            "min_samples_split": {"type": "int"},
            "min_samples_leaf": {"type": "int"},
        }
    }

    params_config = default_model_params.get(model_type, {})

    for param, param_config in params_config.items():
        param_type = param_config.get("type", "str")
        label = param_config.get("label", param)

        default_val = param_config.get("value")
        match param_type:
            case "int":
                optional_params[param] = st.number_input(label, value=default_val if default_val is not None else 5, key=f"opt_{model_type}_{param}")
            case "float":
                optional_params[param] = st.number_input(label, value=default_val if default_val is not None else 0.8, key=f"opt_{model_type}_{param}")
            case "bool":
                optional_params[param] = st.checkbox(label, value=default_val if default_val is not None else True, key=f"opt_{model_type}_{param}")
            case "str":
                optional_params[param] = st.text_input(label, value=default_val or "", key=f"opt_{model_type}_{param}")
            case "select":
                options = param_config.get("options", [])
                optional_params[param] = st.selectbox(label, options, key=f"opt_{model_type}_{param}")
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
                headers = get_auth_headers()
                response = requests.post(
                    API_CREATE_URL,
                    data=data,
                    files=files,
                    headers=headers
                )

            if response.status_code == 200:
                result = response.json()
                st.success("✅ Model training completed successfully!")
                st.json(result)
                tokens_deducted = result.get("tokens_deducted", 0)
                if tokens_deducted:
                    st.info(f"Tokens deducted: {tokens_deducted}")
            elif response.status_code == 401:
                logout_and_rerun()
            else:
                st.error(f"Training failed: {response.text}")