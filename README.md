# ML Training & Prediction Platform — Final Project

**AI Developer Course · Final Project Submission**

**Author:** Shani Staretz

---

## Abstract

This project is a **full-stack ML platform** for training and running predictions with multiple machine-learning model types. It demonstrates REST API design, authentication and authorization, database-backed user and model management, and a modern Streamlit client—submitted as the final project for the AI Developer course.

Users register, receive tokens, and spend them to **train** models (Linear Regression, KNN, Logistic Regression, Random Forest) from CSV data and to **run predictions** with their trained models. Admins can manage users and token balances. All ML operations and user data are persisted via PostgreSQL with JWT-secured APIs.

---

## Features

### Server (FastAPI)
- **Authentication:** Registration, login (JWT), authenticated password reset, bcrypt hashing (72-byte safe).
- **Tokens:** New users get 15 tokens; training costs 1, prediction costs 5; balance at `/user/tokens`. Atomic add/deduct to avoid lost updates under concurrency.
- **Models:** Train **Linear Regression**, **KNN**, **Logistic Regression**, and **Random Forest** from CSV; optional hyperparameters per type; metrics (R², MSE, MAE) saved and returned.
- **Prediction:** Use only your trained models; ownership checked on every call; token deduction is atomic.
- **Admin:** List users (optional filter by min tokens), add tokens, reset user password, delete user (admin-only; cannot delete self).

### Client (Streamlit)
- **Auth:** Login / Register / Reset password in sidebar; token count; session restored from file cache; 401 → logout and rerun.
- **Train:** Upload CSV, choose features/label, model type, optional params; train and see metrics (R², MSE, MAE).
- **Predict:** Select model (friendly labels with type and date), fill feature values (with legacy-model and empty-value handling), run prediction; delete model with confirmation.
- **Admin (if admin user):** Filter users by token count; add tokens, reset password, delete user per user; action selectbox kept in sync when options change (e.g. current user has no “Delete”).

---

## Technologies

| Layer        | Stack |
|-------------|--------|
| **Backend** | FastAPI, PyJWT, bcrypt, PostgreSQL (psycopg2, connection pool), scikit-learn, pandas, joblib |
| **Frontend**| Streamlit, requests |
| **Config**  | python-dotenv; server `config.py`; client `API_BASE_URL` and `build_urls()` |

---

## Folder Structure

```
FinalProject/
├── server/
│   ├── main.py              # FastAPI app, register_routers, startup (init_db)
│   ├── config.py            # Env (JWT, DB, paths)
│   ├── logging.py           # Logging setup and get_logger
│   ├── init_db.py           # Create tables; bootstrap admin if ADMIN_EMAIL/PASSWORD set
│   ├── api/
│   │   └── __init__.py      # register_routers(app)
│   ├── admin/
│   │   └── routes.py        # Admin endpoints
│   ├── users/
│   │   ├── routes.py        # User endpoints
│   │   ├── repository.py    # User DB (atomic token ops)
│   │   └── models.py        # Pydantic request/response
│   ├── models/              # Trained model resource
│   │   ├── routes.py        # Create, predict, list, delete
│   │   └── repository.py    # Model records + file paths
│   ├── ml/                  # Machine learning (no HTTP/DB)
│   │   ├── base_trainer.py  # Train/predict pipeline
│   │   ├── helpers.py       # CSV parse, optional params
│   │   ├── model_classes.py # MODEL_CLASSES registry
│   │   ├── knn_model.py
│   │   ├── linear_regression_model.py
│   │   ├── logistic_model.py
│   │   └── random_forest_model.py
│   ├── security/
│   │   ├── jwt_auth.py
│   │   ├── admin_auth.py
│   │   └── passwords.py
│   ├── db/
│   │   ├── connection.py    # Connection pool
│   │   └── schema.py        # Table definitions
│   ├── train_models/        # Saved .pkl files
│   ├── metrics/             # Per-model metrics .json
│   └── logs/                # app.log
├── client/
│   ├── app.py               # Streamlit entry, tabs (Train, Predict, Admin if admin)
│   ├── config.py            # API base URL (env API_BASE_URL)
│   ├── api.py               # All HTTP calls to server
│   ├── auth.py              # Session, cache, login/logout, 401 handling
│   ├── components/
│   │   └── auth_header.py   # Sidebar auth UI
│   └── tabs/
│       ├── train_tab.py
│       ├── predict_tab.py
│       └── admin_tab.py
├── data/                    # Sample CSVs (e.g. user_decision_classification, health_lifestyle)
├── requirements.txt
├── .env                     # Create this (see below)
└── README.md
```

---

## Installation

1. **Clone and enter project**
   ```bash
   git clone https://github.com/ShaniStaretz-ai/FinalProject.git
   cd FinalProject
   ```

2. **Virtual environment (recommended)**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **PostgreSQL**
   - Install PostgreSQL and create a database.
   - Note host, port, database name, user, and password.

5. **Create `.env` in project root**
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password

   JWT_SECRET=your-secret-key-change-in-production
   JWT_ALGORITHM=HS256
   JWT_EXP_MINUTES=60

   # Optional: bootstrap one admin when DB has no admins (at server startup)
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=your-admin-password-min-4-chars
   ```
   **Required:** `JWT_SECRET` must be set or the server will not start.

6. **Database tables** are created automatically on server startup. If `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set and no admin exists yet, one admin user is created at startup.

---

## Running the Project

From the **project root**:

1. **Start the API server**
   ```bash
   uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - API: http://127.0.0.1:8000  
   - Swagger: http://127.0.0.1:8000/docs  
   - ReDoc: http://127.0.0.1:8000/redoc  

2. **Start the Streamlit client**
   ```bash
   streamlit run client/app.py
   ```
   - App: http://localhost:8501  

**Client API URL:** Default is `http://127.0.0.1:8000`. Override with env var `API_BASE_URL`.

---

## API Endpoints (Summary)

| Area   | Method | Endpoint                          | Auth   | Description                    |
|--------|--------|-----------------------------------|--------|--------------------------------|
| Users  | POST   | `/user/create`                    | No     | Register                       |
| Users  | POST   | `/user/login`                     | No     | Login, get JWT                 |
| Users  | GET    | `/user/tokens`                    | Bearer | Get token balance              |
| Users  | POST   | `/user/reset_password`            | Bearer | Reset own password             |
| Users  | DELETE | `/user/remove_user`               | Bearer | Delete another user            |
| Models | GET    | `/models`                         | No     | List model types + params      |
| Models | GET    | `/trained`                        | Bearer | List your trained models       |
| Models | GET    | `/trained/{model_name}`           | Bearer | Model details + feature_cols   |
| Models | POST   | `/create`                         | Bearer | Train model (1 token)          |
| Models | POST   | `/predict/{model_name}`           | Bearer | Predict (5 tokens)             |
| Models | DELETE | `/delete/{model_name}`            | Bearer | Delete model                   |
| Admin  | GET    | `/admin/users`                    | Admin  | List users (optional min_tokens) |
| Admin  | POST   | `/admin/users/{id}/tokens`        | Admin  | Add tokens to user             |
| Admin  | POST   | `/admin/users/{id}/reset_password`| Admin  | Reset user password            |
| Admin  | DELETE | `/admin/users/{id}`               | Admin  | Delete user                    |

**Auth:** Send JWT in header: `Authorization: Bearer <token>`.

**Train** (multipart/form-data): `model_type`, `feature_cols` (JSON array or comma-separated), `label_col`, `train_percentage`, `csv_file`, `optional_params` (JSON), optional `model_filename`.

**Predict** (JSON body): `{"features": {"col1": value, ...}}`.

---

## Environment Variables

| Variable         | Required | Description |
|------------------|----------|-------------|
| `DB_HOST`       | Yes*     | PostgreSQL host (default: localhost) |
| `DB_PORT`       | No       | Port (default: 5432) |
| `DB_NAME`       | Yes*     | Database name |
| `DB_USER`       | Yes*     | Database user |
| `DB_PASSWORD`    | Yes*     | Database password |
| `JWT_SECRET`    | **Yes**  | JWT signing key (server exits if missing) |
| `JWT_ALGORITHM` | No       | Default: HS256 |
| `JWT_EXP_MINUTES` | No     | Default: 60 |
| `ADMIN_EMAIL`   | No       | Bootstrap admin email (when no admin exists) |
| `ADMIN_PASSWORD`| No       | Bootstrap admin password (min 4 chars) |
| `API_BASE_URL`  | No (client) | Server URL (default: http://127.0.0.1:8000) |

\* DB vars required for the app; missing `DB_NAME`/`DB_USER` will cause connection to fail.

---

## Model Types and Optional Parameters

| Type           | Optional params (examples)     |
|----------------|--------------------------------|
| linear         | `fit_intercept` (bool)         |
| knn            | `n_neighbors` (int), `weights` (str) |
| logistic       | `C` (float), `max_iter` (int), `solver` (str) |
| random_forest  | `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf` |

Model names: auto `{user_id}_{model_type}_{timestamp}` or custom; feature columns stored for prediction UI.

---

## Security and Robustness

- **Passwords:** bcrypt, min length 4, 72-byte truncation.
- **JWT:** HS256, exp/iat; invalid/expired → generic “Invalid token” to client.
- **Ownership:** Models tied to `user_id`; list/predict/delete only your models.
- **Admin:** Bootstrap via `ADMIN_EMAIL`/`ADMIN_PASSWORD` when no admin exists; admin routes require admin JWT; admin cannot delete self.
- **DB:** Parameterized queries; connection pool; **atomic** token add/deduct (single `UPDATE ... SET tokens = tokens ± amount`).
- **Paths:** Model names sanitized; CSV max 50MB; feature/label validation.

---

## Code Quality and Architecture

- **Server:** Clear separation: routes → repositories / ml; config and db used by repos and ml; atomic token operations in repository.
- **Client:** app → tabs / components → auth + api; only `api.py` performs HTTP; session state kept consistent (e.g. admin action selectbox, legacy empty feature handling).
- Error handling, validation, logging, and type hints used throughout.

---

## Deliverables (Final Project)

- **Working application:** Server + client run as described; full auth, train, predict, and admin flows.
- **Documentation:** This README (setup, run, API, env, security).
- **Codebase:** Structured server and client with ML pipeline, DB, and security integrated.

---

**Shani Staretz · AI Developer Course · Final Project**
