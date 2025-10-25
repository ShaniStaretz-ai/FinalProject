import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.title("Linear Regression REST Client")

tab1, tab2 = st.tabs(["Train Model", "Predict"])

# -----------------------------
# Tab 1: Train Model
# -----------------------------
with tab1:
    # --- File upload ---
    uploaded_file = st.file_uploader("Upload CSV", type="csv")

    # --- Handle file load ---
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✅ File loaded successfully!")
            st.write("### Preview of uploaded data:")
            st.dataframe(df.head())

            all_columns = df.columns.tolist()

            # --- Feature & label selection ---
            feature_cols = st.multiselect("Select feature columns", all_columns, key="feature_cols")
            # --- Prevent selecting all columns ---
            if len(feature_cols) == len(all_columns):
                st.error(
                    "⚠️ You cannot select all columns as features. Please leave at least one column for the label.")
                feature_cols = feature_cols[:-1]  # automatically deselect last chosen column

            # Label options exclude features, but add an empty placeholder first
            label_options = ["-- Select Label Column --"] + [col for col in all_columns if col not in feature_cols]
            label_col = st.selectbox("Select label column", label_options, key="label_col")

            # --- Training parameters ---
            train_percentage = st.slider("Training percentage", 0.1, 0.9, 0.8, 0.05)
            model_filename = st.text_input("Model filename", "linear.pkl")

            # --- Train model button ---
            if st.button("Train Model"):
                # --- Validation ---
                if not feature_cols:
                    st.error("⚠️ Please select at least one feature column before training.")
                elif not label_col:
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

                    st.write("Sending request to API:", payload)
                    try:
                        response = requests.post(API_URL, json=payload)
                        if response.status_code == 200:
                            st.success("✅ Model trained successfully!")
                            st.json(response.json())
                        else:
                            st.error(f"❌ Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error sending request: {e}")

            st.info("💡 Tip: To reset everything, click the ❌ next to the uploaded file name above.")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    else:
        st.info("👆 Upload a CSV file to start training.")
# -----------------------------
# Tab 2: Predict with dropdowns
# -----------------------------
with tab2:
    st.header("Predict via API")

    # Upload CSV to get column info (for dropdowns)
    csv_file = st.file_uploader("Upload CSV for feature values", type="csv", key="csv_for_dropdowns")
    if csv_file:
        df = pd.read_csv(csv_file)
        feature_cols = st.multiselect("Select feature columns", df.columns.tolist())

        input_features = {}
        for col in feature_cols:
            if df[col].dtype == "object":  # categorical → dropdown
                options = df[col].dropna().unique().tolist()
                input_features[col] = st.selectbox(f"{col}", options)
            else:  # numeric → number input
                min_val = float(df[col].min())
                max_val = float(df[col].max())
                step = (max_val - min_val) / 100 if max_val != min_val else 1
                input_features[col] = st.number_input(f"{col}", min_value=min_val, max_value=max_val, value=min_val, step=step)

        if st.button("Predict"):
            try:
                response = requests.post(f"{API_URL}/predict", json={"features": input_features})
                if response.ok:
                    st.success(f"Prediction: {response.json()['prediction']}")
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")
