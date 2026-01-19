# FinalProject
Final Project: FastAPI Server for Model Training and Prediction

Created by: Shani Staretz

# Linear Regression REST API & Streamlit Client

A full-stack project to **train and predict Linear Regression models** via a REST API and a Streamlit front-end.  

- **Server:** FastAPI API to train and predict models with JWT authentication.  
- **Client:** Streamlit app to interact with the API, upload CSVs, train models, and make predictions.

---

## Features

### Server (FastAPI)
- **Authentication System:**
  - User registration and login with JWT tokens
  - Password hashing using bcrypt
  - Protected endpoints requiring authentication
  - Token-based authentication via HTTPBearer
- **Model Training:**
  - Train Linear Regression and KNN models from CSV files
  - Automatic handling of numeric, categorical, and date columns
  - Returns model metrics: R² score, Mean Squared Error (MSE), Mean Absolute Error (MAE)
- **Prediction:**
  - Predict using trained models
  - Support for multiple model types

### Client (Streamlit)
- Upload CSV files and select feature/label columns dynamically
- Prevent selection of all columns as features
- Train models and visualize metrics
- Predict using trained models with dynamic input fields
- Display line plots for numeric features
- Session state preserves data across tabs
- Automatic reset when the file is removed

---

## Folder Structure

```
FinalProject/
├─ server/
│ ├─ main.py                    # FastAPI server
│ ├─ config.py                  # Configuration settings
│ ├─ models/                    # ML model implementations
│ │ ├─ base_trainer.py
│ │ ├─ linear_regression_model.py
│ │ ├─ knn_model.py
│ │ └─ model_registry.py
│ ├─ users/                     # User management
│ │ ├─ routes.py                 # User endpoints
│ │ ├─ repository.py             # Database operations
│ │ └─ models.py                 # Pydantic models
│ ├─ security/                  # Authentication & security
│ │ ├─ jwt_auth.py              # JWT token management
│ │ └─ passwords.py              # Password hashing
│ ├─ db/                        # Database
│ │ ├─ connection.py            # Database connection
│ │ ├─ schema.py                # Database schema
│ │ └─ init_db.py               # Database initialization
│ └─ train_models/              # Saved trained models
├─ client/
│ ├─ app.py                     # Streamlit app
│ ├─ config.py                  # Client configuration
│ └─ tabs/
│   ├─ train_tab.py             # Train Model tab
│   └─ predict_tab.py           # Predict tab
├─ requirements.txt
├─ .env                         # Environment variables (create this)
└─ README.md
```

---

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/ShaniStaretz-ai/FinalProject.git
cd FinalProject
```

2. **Create a virtual environment** (recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL database**
   - Install PostgreSQL if not already installed
   - Create a database for the project
   - Note the database credentials

5. **Create `.env` file** in the project root:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# JWT Configuration
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60
```

6. **Initialize the database**
```bash
cd server
python init_db.py
```

---

## Running the Server

1. **Start the FastAPI server:**
```bash
cd server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

2. **Access the API:**
   - API: http://127.0.0.1:8000
   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

---

## API Endpoints

### Authentication Endpoints

#### Create User
```http
POST /user/create
Content-Type: application/json

{
  "email": "user@example.com",
  "pwd": "your_password"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User created successfully. Please log in to get an access token.",
  "email": "user@example.com"
}
```

#### Login
```http
POST /user/login
Content-Type: application/json

{
  "email": "user@example.com",
  "pwd": "your_password"
}
```

**Response:**
```json
{
  "status": "OK",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get User Tokens (Protected)
```http
GET /user/tokens
Authorization: Bearer <your_access_token>
```

**Response:**
```json
{
  "username": "user@example.com",
  "tokens": 15
}
```

#### Delete User (Protected)
```http
DELETE /user/remove_user
Authorization: Bearer <your_access_token>
```

### Model Training & Prediction Endpoints

#### Get Available Models
```http
GET /models
```

#### Get Trained Models
```http
GET /trained
```

#### Train Model
```http
POST /create
Content-Type: multipart/form-data

model_type: linear (or knn)
feature_cols: ["column1", "column2"]
label_col: target_column
train_percentage: 0.8
csv_file: <file>
optional_params: {}
```

#### Predict
```http
POST /predict/{model_name}
Content-Type: application/json
Authorization: Bearer <your_access_token>

{
  "features": {
    "column1": 10,
    "column2": "value"
  }
}
```

---

## Using Swagger UI

1. **Access Swagger UI:** http://127.0.0.1:8000/docs

2. **Authenticate:**
   - Click the **"Authorize"** button at the top right
   - In the dialog, paste your JWT token in the **"Value"** field
   - Click **"Authorize"** then **"Close"**
   - Your token will now be included in all authenticated requests

3. **Test Endpoints:**
   - All endpoints are interactive
   - Protected endpoints will automatically use your token
   - You can test authentication, model training, and predictions

---

## Running the Client

1. **Start Streamlit:**
```bash
cd client
streamlit run app.py
```

2. **Access the client:** http://localhost:8501

3. **Tabs:**
   - **Tab 1: Train Model** - Upload CSV, select features, train models
   - **Tab 2: Predict** - Use trained models to make predictions

---

## Usage

### Authentication Flow

1. **Create an account:**
   ```bash
   POST /user/create
   {
     "email": "user@example.com",
     "pwd": "password123"
   }
   ```

2. **Login to get token:**
   ```bash
   POST /user/login
   {
     "email": "user@example.com",
     "pwd": "password123"
   }
   ```
   Copy the `access_token` from the response.

3. **Use token for protected endpoints:**
   - Include in header: `Authorization: Bearer <token>`
   - Or use Swagger UI's "Authorize" button

### Training Models

1. Upload a CSV file via `/create` endpoint or Streamlit client
2. Select feature columns and label column
3. Set training percentage and model type (linear or knn)
4. Click Train Model
5. Model metrics (R², MSE, MAE) are displayed
6. Model is saved to `server/train_models/`

### Prediction

1. Fill in feature values for prediction (numeric, categorical, or date)
2. Enter the trained model filename
3. Click Predict to get results

### Notes

- Dates are converted to Unix timestamps automatically
- Numeric columns default to mean values for prediction inputs
- Categorical columns appear as dropdowns of unique values
- Removing the uploaded file resets all tabs automatically
- Passwords must be at least 4 characters
- JWT tokens expire after 60 minutes (configurable via `JWT_EXP_MINUTES`)

---

## Security Features

- **Password Hashing:** Bcrypt with automatic 72-byte truncation
- **JWT Tokens:** Secure token-based authentication using PyJWT
- **Protected Endpoints:** User-specific data access
- **Database Transactions:** Proper commit/rollback handling

---

## Technologies Used

- **Backend:** FastAPI, PyJWT, bcrypt, PostgreSQL, scikit-learn, pandas
- **Frontend:** Streamlit
- **Database:** PostgreSQL with psycopg2
- **Authentication:** JWT tokens with HTTPBearer

---

## Environment Variables

Required environment variables (in `.env` file):

- `DB_HOST` - PostgreSQL host
- `DB_PORT` - PostgreSQL port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `JWT_SECRET` - Secret key for JWT signing (change in production!)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_EXP_MINUTES` - Token expiration time in minutes (default: 60)