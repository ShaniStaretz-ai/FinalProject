import streamlit as st
import requests
import json
from datetime import datetime
from auth import is_authenticated, get_auth_headers

def show_predict_tab(urls):
    API_PREDICT_URL = urls["PREDICT"]
    API_TRAINED_URL = urls["TRAINED"]
    API_MODEL_DETAILS_URL = urls["MODEL_DETAILS"]
    API_DELETE_URL = urls["DELETE_MODEL"]
    st.header("Predict Using a Trained Model")

    # Check authentication
    if not is_authenticated():
        st.warning("⚠️ Please log in to view and use trained models.")
        return

    # Fetch trained models dynamically
    trained_models = []
    try:
        headers = get_auth_headers()
        response = requests.get(API_TRAINED_URL, headers=headers)
        if response.status_code == 200:
            # /trained endpoint returns a list directly, not a dict
            trained_models = response.json()
        elif response.status_code == 401:
            st.error("Authentication failed. Please log in again.")
            return
        else:
            st.warning(f"Could not fetch trained models: {response.text}")
    except Exception as e:
        st.warning(f"Error fetching trained models: {e}")

    if not trained_models:
        st.info("No trained models available. Please train a model first.")
        return

    # Create two columns: one for model selection, one for delete button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        model_name = st.selectbox("Select a trained model", trained_models)
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        delete_button = st.button("🗑️ Delete", key="delete_model_btn", type="secondary")
    
    # Handle model deletion with confirmation
    if delete_button and model_name:
        # Store the model to delete in session state for confirmation
        if "model_to_delete" not in st.session_state or st.session_state.model_to_delete != model_name:
            st.session_state.model_to_delete = model_name
            st.session_state.show_delete_confirm = True
    
    # Show confirmation dialog if needed
    if st.session_state.get("show_delete_confirm", False) and st.session_state.get("model_to_delete"):
        model_to_delete = st.session_state.model_to_delete
        st.warning(f"⚠️ **Are you sure you want to delete model '{model_to_delete}'?**")
        st.warning("This action cannot be undone. The model file and database record will be permanently deleted.")
        
        col_confirm, col_cancel = st.columns(2)
        
        with col_confirm:
            if st.button("✅ Yes, Delete", key="confirm_delete", type="primary"):
                try:
                    headers = get_auth_headers()
                    response = requests.delete(
                        f"{API_DELETE_URL}/{model_to_delete}",
                        headers=headers
                    )
                    if response.status_code == 200:
                        st.success(f"✅ Model '{model_to_delete}' deleted successfully!")
                        # Clear session state
                        st.session_state.model_to_delete = None
                        st.session_state.show_delete_confirm = False
                        st.rerun()  # Refresh the page to update the model list
                    elif response.status_code == 401:
                        st.error("Authentication failed. Please log in again.")
                        st.session_state.show_delete_confirm = False
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

    # Fetch model details to get feature columns
    feature_cols = []
    model_details = None
    if model_name:
        try:
            headers = get_auth_headers()
            response = requests.get(
                f"{API_MODEL_DETAILS_URL}/{model_name}",
                headers=headers
            )
            if response.status_code == 200:
                model_details = response.json()
                feature_cols = model_details.get("feature_cols", [])
            elif response.status_code == 404:
                st.error(f"Model '{model_name}' not found or you don't have access to it.")
                return
        except Exception as e:
            st.warning(f"Error fetching model details: {e}")

    st.subheader("Input Feature Values")
    
    # Add examples expander
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
                try:
                    value = float(value)
                except ValueError:
                    pass
                features[key] = value
    else:
        st.info(f"Enter values for {len(feature_cols)} feature(s) used during training:")
        features = {}
        for i, col_name in enumerate(feature_cols):
            # Determine input type based on column name
            col_lower = col_name.lower()
            if "date" in col_lower:
                # Date input - convert to timestamp
                date_val = st.date_input(f"{col_name} (date)", key=f"feat_date_{i}")
                if date_val:
                    # Convert date to datetime at midnight, then to timestamp
                    dt = datetime.combine(date_val, datetime.min.time())
                    features[col_name] = int(dt.timestamp())
                else:
                    features[col_name] = 0
            else:
                # Try numeric input first, fallback to text
                # Determine if it's likely numeric or categorical based on name
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
                        # Try to convert to float
                        features[col_name] = float(value)
                    except ValueError:
                        # Keep as string for categorical features
                        features[col_name] = value
                else:
                    features[col_name] = None

    optional_params = {}
    # Check model_type from model_details instead of model_name
    # Model names follow format: {user_id}_{model_type}_{timestamp}, so we can't use startswith
    if model_details and model_details.get("model_type") == "knn":
        optional_params["n_neighbors"] = st.number_input("n_neighbors (KNN)", 1, 50, 5)
        optional_params["weights"] = st.selectbox("weights (KNN)", ["uniform", "distance"])

    if st.button("Predict"):
        # Filter out None values
        features = {k: v for k, v in features.items() if v is not None}
        
        if not features:
            st.error("Please provide values for at least one feature")
        else:
            payload = {"features": features, **optional_params}
            try:
                headers = get_auth_headers()
                response = requests.post(
                    f"{API_PREDICT_URL}/{model_name}",
                    json=payload,
                    headers=headers
                )
                if response.status_code == 200:
                    result = response.json()
                    prediction = result.get("prediction")
                    tokens_deducted = result.get("tokens_deducted", 0)
                    st.success(f"✅ Prediction: {prediction:.4f}")
                    if tokens_deducted:
                        st.info(f"Tokens deducted: {tokens_deducted}")
                elif response.status_code == 401:
                    st.error("Authentication failed. Please log in again.")
                else:
                    st.error(f"❌ Prediction failed: {response.text}")
            except Exception as e:
                st.error(f"Error sending request: {e}")
