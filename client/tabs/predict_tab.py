import streamlit as st
import pandas as pd
import requests

def show_predict_tab(api_predict_url):
    st.header("Predict Using Trained Model")

    if "training_completed" in st.session_state and st.session_state.training_completed:
        df = st.session_state.uploaded_df
        feature_cols = st.session_state.feature_cols
        st.success("✅ Model training completed! Fill feature values to predict.")
        # Input feature values
        st.subheader("🧠 Input Feature Values")
        features = {}
        for col in feature_cols:
            col_type = df[col].dtype
            if pd.api.types.is_numeric_dtype(col_type):
                val = st.number_input(f"{col}", value=float(df[col].mean()))
            elif "date" in col.lower():
                val = st.date_input(f"{col}")
                val = int(pd.Timestamp(val).timestamp())
            else:
                options = sorted(df[col].dropna().unique())
                val = st.selectbox(f"{col}", options)
            features[col] = val

        model_filename = st.text_input("Enter model filename", "linear.pkl")

        if st.button("Predict"):
            if not model_filename.strip():
                st.error("⚠️ Please enter the model filename.")
            else:
                payload = {"model_filename": model_filename, "features": features}
                try:
                    response = requests.post(api_predict_url, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Prediction successful!")
                        prediction = result.get("prediction")
                        st.metric("Predicted Value", f"{prediction:.4f}")
                    else:
                        st.error(f"❌ Error: {response.text}")
                except Exception as e:
                    st.error(f"❌ Request failed: {e}")
    else:
        st.warning("⚠️ Complete model training first in the **Train Model** tab.")
