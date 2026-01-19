import streamlit as st
import requests

def show_predict_tab(urls):
    API_PREDICT_URL=urls["PREDICT"]
    API_MODELS_URL = urls["MODELS"]
    st.header("Predict Using a Trained Model")

    # Fetch trained models dynamically
    trained_models = []
    try:
        response = requests.get(API_MODELS_URL)
        if response.status_code == 200:
            trained_models = response.json().get("trained_models", [])
        else:
            st.warning(f"Could not fetch trained models: {response.text}")
    except Exception as e:
        st.warning(f"Error fetching trained models: {e}")

    if not trained_models:
        st.info("No trained models available. Please train a model first.")
        return

    model_name = st.selectbox("Select a trained model", trained_models)

    st.subheader("Input Feature Values")
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

    optional_params = {}
    if model_name.lower().startswith("knn"):
        optional_params["n_neighbors"] = st.number_input("n_neighbors (KNN)", 1, 50, 5)
        optional_params["weights"] = st.selectbox("weights (KNN)", ["uniform", "distance"])

    if st.button("Predict"):
        if not features:
            st.error("Provide feature values")
        else:
            payload = {"features": features, **optional_params}
            try:
                response = requests.post(f"{API_PREDICT_URL}/{model_name}", json=payload)
                if response.status_code == 200:
                    prediction = response.json().get("prediction")
                    st.success(f"Prediction: {prediction}")
                else:
                    st.error(f"❌ Prediction failed: {response.text}")
            except Exception as e:
                st.error(f"Error sending request: {e}")
