import streamlit as st
import pandas as pd
import os
import requests

def show_train_tab(api_create_url):
    st.header("Train a New Model via API")

    # --- File upload ---
    uploaded_file = st.file_uploader("Upload CSV", type="csv")

    # --- Handle temporary path in session state ---
    if "temp_path" not in st.session_state:
        st.session_state.temp_path = None

    # --- File removed → delete temp file ---
    if uploaded_file is None and st.session_state.temp_path:
        if os.path.exists(st.session_state.temp_path):
            os.remove(st.session_state.temp_path)
        st.session_state.temp_path = None
        for key in ["training_completed", "uploaded_df", "feature_cols"]:
            if key in st.session_state:
                del st.session_state[key]

    # --- File uploaded ---
    if uploaded_file:
        try:
            # Save temporarily
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.temp_path = temp_path

            # Read CSV
            df = pd.read_csv(temp_path)
            st.success("✅ File loaded successfully!")
            st.write("### Preview of uploaded data:")
            st.dataframe(df.head())

            # --- Feature & label selection ---
            all_columns = df.columns.tolist()
            feature_cols = st.multiselect("Select feature columns", all_columns, key="feature_cols_widget")
            if len(feature_cols) == len(all_columns):
                st.error("⚠️ Cannot select all columns as features; leave at least one for the label.")
                feature_cols = feature_cols[:-1]

            label_options = ["-- Select Label Column --"] + [col for col in all_columns if col not in feature_cols]
            label_col = st.selectbox("Select label column", label_options, key="label_col_widget")

            train_percentage = st.slider("Training percentage", 0.1, 0.9, 0.8, 0.05)
            model_filename = st.text_input("Model filename", "linear.pkl")

            # --- Train button ---
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
                        "csv_file": os.path.abspath(temp_path),  # send full path
                        "feature_cols": feature_cols,
                        "label_col": label_col,
                        "train_percentage": train_percentage,
                        "model_filename": model_filename,
                    }
                    try:
                        response = requests.post(api_create_url, json=payload)
                        if response.status_code == 200:
                            res = response.json()
                            st.success("✅ Model trained successfully!")

                            # --- Display metrics ---
                            if "metrics" in res:
                                st.subheader("📊 Model Metrics")
                                metrics = res["metrics"]
                                st.metric("R² Score", f"{metrics.get('r2_score',0):.4f}")
                                st.metric("MSE", f"{metrics.get('mean_squared_error',0):.2f}")
                                st.metric("MAE", f"{metrics.get('mean_absolute_error',0):.2f}")

                            # Save session state
                            st.session_state.training_completed = True
                            st.session_state.uploaded_df = df
                            st.session_state.feature_cols = feature_cols

                            # Optional: delete temp file after training
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                                st.session_state.temp_path = None

                        else:
                            st.error(f"❌ Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error sending request: {e}")

            st.info("💡 Tip: Click ❌ near the uploaded file name to reset everything.")

        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    else:
        st.info("👆 Upload a CSV file to start training.")
