ML_USER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ml_user (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    pwd TEXT NOT NULL CHECK (char_length(pwd) >= 4),
    tokens INTEGER NOT NULL DEFAULT 0
);
"""

ML_MODEL_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ml_model (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES ml_user(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    feature_cols TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, model_name)
);
"""