import streamlit as st
import requests
import json
import os
import pandas as pd

def show_predict_tab(api_predict_url, api_models_url=None):
    st.header("Predict using a Trained Model")

    # --- File upload (optional: for dynamic features) ---
    uploaded_file = st.file_uploader("Upload CSV (optional, for feature preview)", type="csv")

    if uploaded_file:
        try:
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            df = pd.read_csv(temp_path)
            st.success("✅ File loaded successfully!")
            st.write("### Preview of uploaded data:")
            st.dataframe(df.head())

            # Keep temp_path in session state
            st.session_state.temp_path = temp_path
            feature_columns = df.columns.tolist()
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            feature_columns = []
    else:
        feature_columns = []

    # --- Fetch supported models only if a file was loaded ---
    if uploaded_file and api_models_url:
        try:
            response = requests.get(api_models_url)
            if response.status_code == 200:
                supported_models = response.json().get("supported_models", [])
            else:
                st.warning("Unable to fetch supported models. Using default 'linear'.")
                supported_models = ["linear"]
        except Exception as e:
            st.warning(f"Error fetching supported models: {e}")
            supported_models = ["linear"]
    else:
        supported_models = []

    if not supported_models:
        st.info("⚠️ Load a CSV file to see available models.")
        return

    # --- Model selection ---
    selected_model = st.selectbox("Select model", supported_models, index=0)

    # --- Feature input ---
    if feature_columns:
        st.write("### Feature values")
        features = {}
        for col in feature_columns:
            val = st.text_input(f"{col}", "")
            if val.strip() != "":
                # try to convert numeric values
                try:
                    features[col] = float(val)
                except:
                    features[col] = val
    else:
        feature_input = st.text_area(
            "Input features as JSON",
            '{"age":30,"salary":50000,"city":"Chicago"}'
        )
        try:
            features = json.loads(feature_input) if feature_input.strip() else {}
        except:
            features = {}

    if st.button("Predict"):
        if not features:
            st.error("⚠️ Please provide feature values.")
            return

        # Construct model filename automatically
        model_filename = f"{selected_model}.pkl"
        payload = {"features": features}

        try:
            response = requests.post(f"{api_predict_url}/{model_filename}", json=payload)
            if response.status_code == 200:
                res = response.json()
                st.success(f"✅ Prediction: {res.get('prediction')}")
            elif response.status_code == 404:
                st.error(f"❌ Model file not found: {model_filename}")
            else:
                st.error(f"❌ Error: {response.text}")
        except Exception as e:
            st.error(f"Error sending request: {e}")
