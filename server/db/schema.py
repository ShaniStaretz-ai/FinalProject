ML_USER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ml_user (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    pwd TEXT NOT NULL CHECK (char_length(pwd) >= 4),
    tokens INTEGER NOT NULL DEFAULT 0
);
"""
