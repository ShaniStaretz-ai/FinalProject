import streamlit as st
import json
import pandas as pd
from auth import is_authenticated, get_auth_headers, logout_and_rerun
from api import get_models, create_model

def show_train_tab(urls):
    st.header("Train Model")
    if not is_authenticated():
        st.warning("⚠️ Please log in to train models.")
        return
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if not uploaded_file:
        st.info("Please upload a CSV file to continue.")
        return

    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())
    columns = df.columns.tolist()
    feature_cols = st.multiselect("Select feature columns", columns)
    label_col_options = [c for c in columns if c not in feature_cols]
    if not label_col_options:
        st.error("Please deselect some feature columns to have at least one label column.")
        return
    label_col = st.selectbox("Select label column", label_col_options)
    train_percentage = st.slider("Training %", 0.5, 0.95, 0.8, 0.05)
    try:
        response = get_models(urls)
        model_types_data = response.json() if response.status_code == 200 else {}
    except Exception:
        model_types_data = {}

    if not model_types_data:
        model_types_data = {"linear": {"params": {}}}

    model_type = st.selectbox("Select model type", list(model_types_data.keys()))
    st.subheader("Optional Parameters")

    default_model_params = {
        "linear": {"fit_intercept": {"type": "bool"}},
        "knn": {
            "n_neighbors": {"type": "int", "value": 5},
            "weights": {"type": "select", "options": ["uniform", "distance"]}
        },
        "logistic": {
            "C": {"type": "float", "label": "C (inverse of regularization strength; smaller = stronger regularization)", "value": 1.0},
            "max_iter": {"type": "int", "label": "max_iter (maximum number of iterations for the solver to converge)", "value": 100},
            "solver": {"type": "str", "label": "solver (algorithm: lbfgs, liblinear, newton-cg, sag, or saga)", "value": "lbfgs"},
        },
        "random_forest": {
            "n_estimators": {"type": "int", "value": 100},
            "max_depth": {"type": "int", "value": 0},
            "min_samples_split": {"type": "int", "value": 2},
            "min_samples_leaf": {"type": "int", "value": 1},
        }
    }
    api_params = model_types_data.get(model_type, {}).get("params", {})
    client_defaults = default_model_params.get(model_type, {})
    params_config = {}
    for param in set(api_params.keys()) | set(client_defaults.keys()):
        client_cfg = client_defaults.get(param) or {}
        ptype = api_params.get(param) or client_cfg.get("type", "str")
        if client_cfg.get("type") == "select" and client_cfg.get("options"):
            ptype = "select"
        params_config[param] = {
            "type": ptype,
            "label": client_cfg.get("label", param),
            "value": client_cfg.get("value"),
            "options": client_cfg.get("options"),
        }

    optional_params = {}
    for param, param_config in params_config.items():
        param_type = param_config.get("type", "str")
        label = param_config.get("label", param)

        default_val = param_config.get("value")
        match param_type:
            case "int":
                optional_params[param] = st.number_input(label, value=default_val if default_val is not None else 5, key=f"opt_{model_type}_{param}", min_value=0)
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
                st.error(f"Parameter '{param}' has unsupported type '{param_type}' and will not be sent. Supported: int, float, bool, str, select.")

    if st.button("Train Model"):
        if not feature_cols or not label_col:
            st.error("Please select feature and label columns.")
        else:
            # Client-side validation of missing data before sending to server
            if df[label_col].isna().any():
                st.error(f"Label column '{label_col}' contains missing values. Please clean the CSV (or remove rows with empty labels) before training.")
                return
            feature_na = df[feature_cols].isna().any()
            cols_with_na = [col for col, has_na in feature_na.items() if has_na]
            if cols_with_na:
                st.error(f"Feature column(s) {cols_with_na} contain missing values. Please clean or impute them before training.")
                return

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
                response = create_model(urls, headers, data, files)

            if response.status_code == 200:
                result = response.json()
                st.success("✅ Model training completed successfully!")
                metrics = result.get("metrics", {})
                if metrics:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("R²", f"{metrics.get('r2_score', 0):.4f}")
                    with col2:
                        st.metric("MSE", f"{metrics.get('mean_squared_error', 0):.4f}")
                    with col3:
                        st.metric("MAE", f"{metrics.get('mean_absolute_error', 0):.4f}")
                tokens_deducted = result.get("tokens_deducted", 0)
                if tokens_deducted:
                    st.info(f"Tokens deducted: {tokens_deducted}")
            elif response.status_code == 401:
                logout_and_rerun()
            else:
                st.error(f"Training failed: {response.text}")