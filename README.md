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
  - Password hashing using bcrypt (72-byte safe)
  - Protected endpoints requiring authentication
  - Token-based authentication via HTTPBearer
  - Users can only access their own models
- **Token System:**
  - New users receive 15 tokens by default
  - Training a model costs 1 token
  - Making a prediction costs 5 tokens
  - Users can check their token balance via `/user/tokens`
- **Model Training:**
  - Train Linear Regression and KNN models from CSV files
  - Automatic handling of numeric, categorical, and date columns
  - Returns model metrics: R² score, Mean Squared Error (MSE), Mean Absolute Error (MAE)
  - Models are automatically associated with the authenticated user
  - Unique model names: `{user_id}_{model_type}_{timestamp}` or custom names
- **Prediction:**
  - Predict using trained models (only your own models)
  - Support for multiple model types
  - Automatic model ownership verification

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
│ │ ├─ model_classes.py
│ │ ├─ routes.py                 # Model endpoints
│ │ └─ repository.py             # Model database operations
│ ├─ core_models/               # Core utilities
│ │ └─ server_logger.py          # Centralized logging
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

# JWT Configuration (REQUIRED - server will not start without JWT_SECRET)
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60
```

   **⚠️ Important:** The `JWT_SECRET` environment variable is **REQUIRED**. The server will not start without it. Use a strong, random secret key for production.

6. **Database initialization**
   - The database tables are automatically created when the server starts
   - Manual initialization (optional): `cd server && python init_db.py`

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
Content-Type: application/json

{
  "user_id": 5
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User with ID 5 deleted"
}
```

**Note:** Users cannot delete their own account. They can only delete other users' accounts.

### Model Training & Prediction Endpoints

#### Get Available Models
```http
GET /models
```

#### Get Trained Models (Protected)
```http
GET /trained
Authorization: Bearer <your_access_token>
```

**Response:** Returns only models owned by the authenticated user
```json
[
  "3_knn_20260119_190735_140414",
  "3_linear_20260119_185500_123456"
]
```

#### Train Model (Protected)
```http
POST /create
Content-Type: multipart/form-data
Authorization: Bearer <your_access_token>

model_type: linear (or knn)
feature_cols: ["column1", "column2"] (or "column1,column2" as comma-separated string)
label_col: target_column
train_percentage: 0.8 (must be between 0 and 1)
csv_file: <file>
optional_params: {} (JSON string, e.g., '{"fit_intercept": true}' for linear)
model_filename: optional_custom_name (optional - if not provided, auto-generated)
```

**Response:**
```json
{
  "status": "success",
  "model_name": "3_knn_20260119_190735_140414",
  "metrics": {
    "r2_score": 0.856,
    "mean_squared_error": 1234.56,
    "mean_absolute_error": 25.43
  },
  "tokens_deducted": 1
}
```

**Model Name Format:**
- Auto-generated: `{user_id}_{model_type}_{YYYYMMDD}_{HHMMSS}_{microseconds}`
- Example: `3_knn_20260119_190735_140414`
- Custom names are sanitized and prefixed with user_id for security

#### Predict (Protected)
```http
POST /predict/{model_name}
Content-Type: application/json
Authorization: Bearer <your_access_token>

{
  "features": {
    "column1": 10,
    "column2": "value"
  },
  "optional_params": {}  // Optional model-specific parameters
}
```

**Response:**
```json
{
  "status": "success",
  "prediction": 123.45,
  "tokens_deducted": 5
}
```

**Note:** You can only predict with models you own. The system verifies ownership before allowing prediction.

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

1. **Authenticate:** Get a JWT token via `/user/login`
2. **Check tokens:** Verify you have enough tokens (1 token required for training)
3. **Upload CSV:** Upload a CSV file via `/create` endpoint or Streamlit client
4. **Select columns:** Choose feature columns and label column
5. **Configure model:**
   - Set training percentage (0.0 to 1.0)
   - Choose model type (linear or knn)
   - Optionally provide a custom model name
   - Set optional parameters (e.g., `fit_intercept` for linear regression)
6. **Train:** Click Train Model (1 token is deducted)
7. **Results:** Model metrics (R², MSE, MAE) are displayed
8. **Storage:** 
   - Model is saved to `server/train_models/{model_name}.pkl`
   - Model record is stored in database with ownership information

### Prediction

1. **Authenticate:** Ensure you have a valid JWT token
2. **Check tokens:** Verify you have enough tokens (5 tokens required for prediction)
3. **Select model:** Choose from your trained models (only your models are accessible)
4. **Fill features:** Enter feature values (numeric, categorical, or date)
5. **Predict:** Click Predict (5 tokens are deducted)
6. **Results:** Prediction value is returned

### Notes

- **Model Ownership:** Each model is associated with the user who created it
- **Model Names:** Auto-generated names include user ID, model type, and timestamp with microseconds for uniqueness
- **Token System:** 
  - Training costs 1 token
  - Prediction costs 5 tokens
  - Check your balance with `/user/tokens`
- **Data Preprocessing:**
  - Dates are converted to Unix timestamps automatically
  - Categorical columns are one-hot encoded
  - Numeric columns are passed through as-is
- **Input Formats:**
  - `feature_cols` can be sent as JSON array: `["age", "salary"]`
  - Or as comma-separated string: `"age,salary"`
- **Passwords:** Must be at least 4 characters (max 72 bytes due to bcrypt limit)
- **JWT Tokens:** Expire after 60 minutes (configurable via `JWT_EXP_MINUTES`)
- **Database:** Tables are automatically created on server startup
- **Logging:** Concise logs with format: `HH:MM:SS | LEVEL | Module | Message`

---

## Security Features

- **Password Hashing:** Bcrypt with automatic 72-byte truncation and UTF-8 safe handling
- **JWT Tokens:** Secure token-based authentication using PyJWT
- **Protected Endpoints:** User-specific data access with ownership verification
- **Database Transactions:** Proper commit/rollback handling
- **Model Ownership:** Users can only access, train, and predict with their own models
- **Input Validation:** Comprehensive validation for all inputs
- **Path Traversal Protection:** Model names are sanitized to prevent directory traversal
- **SQL Injection Prevention:** All queries use parameterized statements

---

## Technologies Used

- **Backend:** FastAPI, PyJWT, bcrypt, PostgreSQL, scikit-learn, pandas, joblib
- **Frontend:** Streamlit
- **Database:** PostgreSQL with psycopg2 (connection pooling recommended for production)
- **Authentication:** JWT tokens with HTTPBearer
- **Logging:** Python logging with centralized configuration
- **Data Processing:** Pandas for CSV handling, scikit-learn for ML models

---

## Environment Variables

Required environment variables (in `.env` file):

- `DB_HOST` - PostgreSQL host
- `DB_PORT` - PostgreSQL port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `JWT_SECRET` - Secret key for JWT signing (REQUIRED - server will not start without it)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_EXP_MINUTES` - Token expiration time in minutes (default: 60)

**Important Notes:**
- `DB_PORT` must be a valid integer (e.g., `5432`)
- `JWT_SECRET` is required - the server will exit with a clear error message if missing
- Database tables are automatically created on server startup
- All database operations use proper transaction management with commit/rollback

---

## Model Name Format

Model names follow a specific format to ensure uniqueness and ownership:

**Auto-generated format:**
```
{user_id}_{model_type}_{YYYYMMDD}_{HHMMSS}_{microseconds}
```

**Example:**
```
3_knn_20260119_190735_140414
```

**Breakdown:**
- `3` - User ID (from database)
- `knn` - Model type (`knn` or `linear`)
- `20260119` - Date (YYYYMMDD)
- `190735` - Time (HHMMSS)
- `140414` - Microseconds (ensures uniqueness within the same second)

**Custom names:**
- If you provide a custom `model_filename`, it's sanitized and prefixed with your user ID
- Format: `{user_id}_{sanitized_filename}`
- This ensures ownership and prevents conflicts

---

## Code Quality

The codebase follows best practices:
- ✅ Comprehensive error handling with proper HTTP status codes
- ✅ Database transaction management (commit/rollback)
- ✅ Input validation and sanitization
- ✅ Centralized logging with concise format
- ✅ Type hints throughout
- ✅ Modular architecture with separation of concerns
- ✅ Security best practices (password hashing, JWT, SQL injection prevention)

For detailed code review findings, see `CODE_REVIEW.md`.