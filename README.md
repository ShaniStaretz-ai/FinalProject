# FinalProject
Final Project: FastAPI Server for Model Training and Prediction

Created by: Shani Staretz
# Linear Regression REST API & Streamlit Client

A full-stack project to **train and predict Linear Regression models** via a REST API and a Streamlit front-end.  

- **Server:** FastAPI API to train and predict models.  
- **Client:** Streamlit app to interact with the API, upload CSVs, train models, and make predictions.

---

## Features

### Server (FastAPI)
- Train Linear Regression models from a CSV file.
- Predict using trained models.
- Automatic handling of numeric, categorical, and date columns.
- Returns model metrics: R² score, Mean Squared Error (MSE), Mean Absolute Error (MAE).

### Client (Streamlit)
- Upload CSV files and select feature/label columns dynamically.
- Prevent selection of all columns as features.
- Train models and visualize metrics.
- Predict using trained models with dynamic input fields.
- Display line plots for numeric features.
- Session state preserves data across tabs.
- Automatic reset when the file is removed.

---

## Folder Structure

FinalProject/
├─ server/
│ ├─ main.py # FastAPI server
│ ├─ linear_regression_model.py # Model training & prediction
├─ client/
│ ├─ app.py # Streamlit app
│ ├─ tabs/
│ │ ├─ train_tab.py # Train Model tab
│ │ └─ predict_tab.py # Predict tab
├─ requirements.txt
└─ README.md


---

## Installation

1.  **Clone the repository**

```bash
git clone https://github.com/ShaniStaretz-ai/FinalProject.git
cd FinalProject
```
2.  **Install dependencies**
```
pip install -r requirements.txt
```
## Running the Server

1.  Go to the server folder:
```
cd server
```
2.  Start FastAPI:
```
uvicorn main:app --port 8000
```
* API endpoints:

  *   /create → POST JSON to train a model
  *   /predict → POST JSON to make predictions

Server runs at http://127.0.0.1:8000.

## Running the Client
1.  Go to the client folder:
```
cd client
```
2.  Start Streamlit:
```
streamlit run app.py
```
* Tab 1: Train Model

* Tab 2: Predict using the trained model

Session state ensures training and prediction data persist until the uploaded file is removed.

## Usage
### Training

1.  Upload a CSV file.

2.  Select feature columns and label column.

3.  Set training percentage and model filename.

4.  Click Train Model.

5.  Model metrics (R², MSE, MAE) are displayed.

### Prediction

1.  Fill in feature values for prediction (numeric, categorical, or date).

2.  Enter the trained model filename.

3.  Click Predict to get results.

4.  Click Train Model.

### Notes

*   Dates are converted to Unix timestamps automatically.

*   Numeric columns default to mean values for prediction inputs.

*   Categorical columns appear as dropdowns of unique values.

*   Removing the uploaded file resets all tabs automatically.