import streamlit as st
import pandas as pd
import os
import requests

def show_train_tab(api_create_url, api_models_url=None):
    st.header("Train a New Model via API")

    # --- File upload ---
    uploaded_file = st.file_uploader("Upload CSV", type="csv")

    if "temp_path" not in st.session_state:
        st.session_state.temp_path = None

    if uploaded_file is None and st.session_state.temp_path:
        if os.path.exists(st.session_state.temp_path):
            os.remove(st.session_state.temp_path)
        st.session_state.temp_path = None
        for key in ["training_completed", "uploaded_df", "feature_cols", "model_name", "selected_model"]:
            if key in st.session_state:
                del st.session_state[key]

    if uploaded_file:
        try:
            # --- Save temp file ---
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.temp_path = temp_path

            # --- Load CSV ---
            df = pd.read_csv(temp_path)
            st.success("✅ File loaded successfully!")
            st.write("### Preview of uploaded data:")
            st.dataframe(df.head())

            # --- Multi-select dropdown for feature columns ---
            all_columns = df.columns.tolist()
            feature_cols = st.multiselect(
                "Select feature columns",
                options=all_columns,
                default=all_columns[:-1]  # default: all except last column
            )

            # --- Label selection ---
            label_options = ["-- Select Label Column --"] + [col for col in all_columns if col not in feature_cols]
            label_col = st.selectbox("Select label column", label_options, key="label_col_widget")

            # --- Training options ---
            train_percentage = st.slider("Training percentage", 0.1, 0.9, 0.8, 0.05)

            # --- Multi-model selection ---
            if api_models_url:
                try:
                    response = requests.get(api_models_url)
                    if response.status_code == 200:
                        supported_models = response.json().get("supported_models", [])
                    else:
                        supported_models = ["linear"]
                except:
                    supported_models = ["linear"]
            else:
                supported_models = ["linear"]

            if not supported_models:
                st.warning("No supported models available.")
                return

            selected_model = st.selectbox("Select model type", supported_models, index=0)
            model_filename = f"{selected_model}.pkl"

            # --- Train button ---
            if st.button("Train Model"):
                # --- Validation ---
                if not feature_cols:
                    st.error("⚠️ Please select at least one feature column.")
                elif label_col == "-- Select Label Column --":
                    st.error("⚠️ Please select a label column.")
                else:
                    payload = {
                        "csv_file": os.path.abspath(temp_path),
                        "feature_cols": feature_cols,
                        "label_col": label_col,
                        "train_percentage": train_percentage,
                        "model_name": selected_model,
                        "model_filename": model_filename
                    }
                    try:
                        response = requests.post(api_create_url, json=payload)
                        if response.status_code == 200:
                            res = response.json()
                            st.success(f"✅ {selected_model} model trained successfully!")

                            if "metrics" in res:
                                st.subheader("📊 Model Metrics")
                                metrics = res["metrics"]
                                st.metric("R² Score", f"{metrics.get('r2_score',0):.4f}")
                                st.metric("MSE", f"{metrics.get('mean_squared_error',0):.2f}")
                                st.metric("MAE", f"{metrics.get('mean_absolute_error',0):.2f}")

                            st.session_state.training_completed = True
                            st.session_state.uploaded_df = df
                            st.session_state.feature_cols = feature_cols
                            st.session_state.model_name = selected_model
                            st.session_state.selected_model = selected_model

                            # Remove temp file
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                                st.session_state.temp_path = None
                        else:
                            st.error(f"❌ Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error sending request: {e}")

            st.info("💡 Tip: Multi-select the columns to include as features.")

        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    else:
        st.info("👆 Upload a CSV file to start training.")
