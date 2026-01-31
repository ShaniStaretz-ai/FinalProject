import streamlit as st
from datetime import datetime
from auth import is_authenticated, get_auth_headers, logout_and_rerun
from api import get_trained_models, get_model_details, predict_model, delete_model


_MODEL_TYPE_LABELS = {
    "knn": "KNN",
    "linear": "Linear",
    "logistic": "Logistic",
    "random_forest": "Random Forest",
}


def _model_display_label(internal_name: str) -> str:
    parts = internal_name.split("_")
    if len(parts) < 5:
        return internal_name
    try:
        date_str = parts[-3]
        time_str = parts[-2]
        model_type_raw = "_".join(parts[1:-3])
        model_type = _MODEL_TYPE_LABELS.get(model_type_raw, model_type_raw.replace("_", " ").title())
        dt = datetime(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]),
                      int(time_str[:2]), int(time_str[2:4]), int(time_str[4:6]))
        friendly_date = dt.strftime("%b %d, %Y · %H:%M")
        return f"{model_type} — {friendly_date}"
    except (ValueError, IndexError):
        return internal_name


def show_predict_tab(urls):
    st.header("Predict Using a Trained Model")
    if not is_authenticated():
        st.warning("⚠️ Please log in to view and use trained models.")
        return
    trained_models = []
    try:
        headers = get_auth_headers()
        response = get_trained_models(urls, headers)
        if response.status_code == 200:
            trained_models = response.json()
        elif response.status_code == 401:
            logout_and_rerun()
        else:
            st.warning(f"Could not fetch trained models: {response.text}")
    except Exception as e:
        st.warning(f"Error fetching trained models: {e}")

    if not trained_models:
        st.info("No trained models available. Please train a model first.")
        return
    col1, col2 = st.columns([3, 1])
    
    with col1:
        model_name = st.selectbox(
            "Select a trained model",
            trained_models,
            format_func=_model_display_label,
            help="Choose a model you previously trained. Each option shows the model type (e.g. KNN, Linear) and when it was trained.",
        )
        st.caption("Pick the model to use for predictions. Labels show model type and training date.")
    
    with col2:
        st.write("")
        st.write("")
        delete_button = st.button("🗑️ Delete", key="delete_model_btn", type="secondary")
    if delete_button and model_name:
        if "model_to_delete" not in st.session_state or st.session_state.model_to_delete != model_name:
            st.session_state.model_to_delete = model_name
            st.session_state.show_delete_confirm = True
    if st.session_state.get("show_delete_confirm", False) and st.session_state.get("model_to_delete"):
        model_to_delete = st.session_state.model_to_delete
        st.warning(f"⚠️ **Are you sure you want to delete model '{_model_display_label(model_to_delete)}'?**")
        st.warning("This action cannot be undone. The model file and database record will be permanently deleted.")
        
        col_confirm, col_cancel = st.columns(2)
        
        with col_confirm:
            if st.button("✅ Yes, Delete", key="confirm_delete", type="primary"):
                try:
                    headers = get_auth_headers()
                    response = delete_model(urls, model_to_delete, headers)
                    if response.status_code == 200:
                        st.success(f"✅ Model '{_model_display_label(model_to_delete)}' deleted successfully!")
                        st.session_state.model_to_delete = None
                        st.session_state.show_delete_confirm = False
                        st.rerun()
                    elif response.status_code == 401:
                        logout_and_rerun()
                    elif response.status_code == 404:
                        st.error(f"Model '{model_to_delete}' not found or you don't have access to it.")
                        st.session_state.show_delete_confirm = False
                    else:
                        st.error(f"❌ Failed to delete model: {response.text}")
                        st.session_state.show_delete_confirm = False
                except Exception as e:
                    st.error(f"Error deleting model: {e}")
                    st.session_state.show_delete_confirm = False
        
        with col_cancel:
            if st.button("❌ Cancel", key="cancel_delete"):
                st.session_state.model_to_delete = None
                st.session_state.show_delete_confirm = False
                st.rerun()

    feature_cols = []
    model_details = None
    if model_name:
        try:
            headers = get_auth_headers()
            response = get_model_details(urls, model_name, headers)
            if response.status_code == 200:
                model_details = response.json()
                feature_cols = model_details.get("feature_cols", [])
            elif response.status_code == 401:
                logout_and_rerun()
            elif response.status_code == 404:
                st.error(f"Model '{model_name}' not found or you don't have access to it.")
                return
            else:
                st.error(f"Could not load model details (status {response.status_code}). Please try again.")
                return
        except Exception as e:
            st.warning(f"Error fetching model details: {e}")
            return

    st.subheader("Input Feature Values")
    with st.expander("📖 See Examples", expanded=False):
        st.markdown("""
        **Example Prediction Values:**
        
        **For Numeric Features** (age, salary, etc.):
        - Enter numbers: `30`, `52000`, `45.5`
        - Example: `age: 30`, `salary: 52000`
        
        **For Categorical Features** (city, category, etc.):
        - Enter text matching training data: `"New York"`, `"Chicago"`, `"Los Angeles"`
        - Must match exactly (case-sensitive)
        - Example: `city: New York`
        
        **For Date Features** (hire_date, start_date, etc.):
        - Use the date picker (automatically converted to timestamp)
        - Example: Select `2020-10-22` from the date picker
        
        **Complete Example:**
        ```
        Model trained with: ["age", "salary", "city", "hire_date"]
        
        Prediction inputs:
        - age: 30
        - salary: 52000
        - city: Los Angeles
        - hire_date: 2018-03-20 (selected from date picker)
        
        Result: Prediction value (e.g., 4200.50)
        ```
        
        **Note:** All features used during training must be provided. The system will validate your inputs before making the prediction.
        """)
    
    if not feature_cols:
        st.info("ℹ️ **Note:** This model was trained before feature column tracking was added. Please enter the feature names and values manually based on what you used during training.")
        st.warning("⚠️ For future models, feature columns will be automatically detected.")
        features = {}
        feature_count = st.number_input("Number of features to input", min_value=1, value=4, step=1)
        for i in range(feature_count):
            key = st.text_input(f"Feature {i+1} name", key=f"feat_name_{i}")
            value = st.text_input(f"Feature {i+1} value", key=f"feat_value_{i}")
            if key:
                if not value or not str(value).strip():
                    features[key] = None
                else:
                    try:
                        features[key] = float(value)
                    except ValueError:
                        features[key] = value
    else:
        st.info(f"Enter values for {len(feature_cols)} feature(s) used during training:")
        features = {}
        for i, col_name in enumerate(feature_cols):
            col_lower = col_name.lower()
            if "date" in col_lower:
                date_val = st.date_input(f"{col_name} (date)", key=f"feat_date_{i}")
                if date_val:
                    dt = datetime.combine(date_val, datetime.min.time())
                    features[col_name] = int(dt.timestamp())
                else:
                    features[col_name] = 0
            else:
                col_lower = col_name.lower()
                if any(keyword in col_lower for keyword in ["age", "salary", "price", "amount", "count", "score", "rate", "percent"]):
                    help_text = f"Enter a number (e.g., 30, 52000, 45.5)"
                elif any(keyword in col_lower for keyword in ["city", "category", "type", "status", "name", "label"]):
                    help_text = f"Enter text matching training data (e.g., 'New York', 'Chicago')"
                else:
                    help_text = "Enter a numeric value or text for categorical features"
                
                value = st.text_input(
                    f"{col_name}",
                    key=f"feat_{i}",
                    help=help_text
                )
                if value:
                    try:
                        features[col_name] = float(value)
                    except ValueError:
                        features[col_name] = value
                else:
                    features[col_name] = None

    if st.button("Predict"):
        features = {k: v for k, v in features.items() if v is not None and v != ""}
        
        if not features:
            st.error("Please provide values for at least one feature")
        else:
            payload = {"features": features}
            try:
                headers = get_auth_headers()
                response = predict_model(urls, model_name, headers, payload)
                if response.status_code == 200:
                    result = response.json()
                    prediction = result.get("prediction")
                    tokens_deducted = result.get("tokens_deducted", 0)
                    st.success(f"✅ Prediction: {prediction:.4f}")
                    if tokens_deducted:
                        st.info(f"Tokens deducted: {tokens_deducted}")
                elif response.status_code == 401:
                    logout_and_rerun()
                else:
                    st.error(f"❌ Prediction failed: {response.text}")
            except Exception as e:
                st.error(f"Error sending request: {e}")
