import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# --- Sidebar: API URL ---
st.sidebar.header("API Settings")
API_BASE_URL = st.sidebar.text_input("API Base URL", "http://127.0.0.1:8000")
CREATE_URL = f"{API_BASE_URL}/create"
PREDICT_URL = f"{API_BASE_URL}/predict"

# --- Tabs ---
tabs = st.tabs(["Train Model", "Predict"])

############################
# --- Tab 1: Train Model ---
############################
with tabs[0]:
    st.header("Train a New Model via API")

    uploaded_file = st.file_uploader("Upload CSV", type="csv")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✅ File loaded successfully!")
            st.write("### Preview of uploaded data:")
            st.dataframe(df.head())

            all_columns = df.columns.tolist()

            # Feature selection widget
            feature_cols = st.multiselect("Select feature columns", all_columns, key="feature_cols_widget")
            if len(feature_cols) == len(all_columns):
                st.error("⚠️ Cannot select all columns as features; leave at least one for the label.")
                feature_cols = feature_cols[:-1]

            # Label selection
            label_options = ["-- Select Label Column --"] + [col for col in all_columns if col not in feature_cols]
            label_col = st.selectbox("Select label column", label_options, key="label_col_widget")

            # Training parameters
            train_percentage = st.slider("Training percentage", 0.1, 0.9, 0.8, 0.05)
            model_filename = st.text_input("Model filename", "linear.pkl")

            # Train button
            if st.button("Train Model"):
                # Validation
                if not feature_cols:
                    st.error("⚠️ Please select at least one feature column.")
                elif label_col == "-- Select Label Column --":
                    st.error("⚠️ Please select a label column.")
                elif not model_filename.strip():
                    st.error("⚠️ Please enter a model filename.")
                else:
                    payload = {
                        "csv_file": uploaded_file.name,
                        "feature_cols": feature_cols,
                        "label_col": label_col,
                        "train_percentage": train_percentage,
                        "model_filename": model_filename,
                    }
                    try:
                        response = requests.post(CREATE_URL, json=payload)
                        if response.status_code == 200:
                            st.success("✅ Model trained successfully!")
                            st.json(response.json())
                            # Save session state AFTER training success
                            st.session_state.training_completed = True
                            st.session_state.uploaded_df = df
                            st.session_state.feature_cols = feature_cols
                        else:
                            st.error(f"❌ Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error sending request: {e}")

            st.info("💡 Tip: Click ❌ near the uploaded file name to reset everything.")

        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    else:
        st.info("👆 Upload a CSV file to start training.")

############################
# --- Tab 2: Predict ---
############################
with tabs[1]:
    st.header("Predict Using Trained Model")

    if "training_completed" in st.session_state and st.session_state.training_completed:
        df = st.session_state.uploaded_df
        feature_cols = st.session_state.feature_cols
        st.success("✅ Model training completed! Fill feature values to predict.")

        # Optional: preview feature columns
        st.subheader("Feature Columns")
        st.dataframe(df[feature_cols].head())

        # Dynamic input fields for feature columns
        st.subheader("🧠 Input Feature Values")
        features = {}
        for col in feature_cols:
            col_type = df[col].dtype

            if pd.api.types.is_numeric_dtype(col_type):
                default_val = float(df[col].mean())
                val = st.number_input(f"{col}", value=default_val)
            elif "date" in col.lower():
                val = st.date_input(f"{col}")
                val = int(pd.Timestamp(val).timestamp())
            else:
                options = sorted(df[col].dropna().unique().tolist())
                val = st.selectbox(f"{col}", options)
            features[col] = val

        # Model filename
        model_filename = st.text_input("Enter model filename", "linear.pkl")

        # Predict button
        if st.button("Predict"):
            if not model_filename.strip():
                st.error("⚠️ Please enter the model filename.")
            else:
                payload = {
                    "model_filename": model_filename,
                    "features": features
                }
                st.write("📤 Sending request to API:")
                st.json(payload)

                try:
                    response = requests.post(PREDICT_URL, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Prediction successful!")
                        st.json(result)
                    else:
                        st.error(f"❌ Error: {response.text}")
                except Exception as e:
                    st.error(f"❌ Request failed: {e}")

    else:
        st.warning("⚠️ Complete model training first in the **Train Model** tab.")
