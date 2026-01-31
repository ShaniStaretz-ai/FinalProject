import logging
from server.db.connection import get_connection, return_connection
from server.db.schema import ML_USER_TABLE_SQL, ML_MODEL_TABLE_SQL
from server.config import ADMIN_EMAIL, ADMIN_PASSWORD
from server.security.passwords import hash_password

logger = logging.getLogger(__name__)


def _ensure_one_admin(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM ml_user WHERE is_admin = TRUE")
        (n,) = cur.fetchone()
        if n > 0:
            logger.info("At least one admin already exists, skipping bootstrap admin")
            return
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        logger.info("ADMIN_EMAIL or ADMIN_PASSWORD not set, skipping bootstrap admin")
        return
    if len(ADMIN_PASSWORD) < 4:
        logger.warning("ADMIN_PASSWORD must be at least 4 characters, skipping bootstrap admin")
        return
    try:
        pwd_hashed = hash_password(ADMIN_PASSWORD)
    except Exception as e:
        logger.warning("Failed to hash admin password: %s", e)
        return
    with conn.cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO ml_user (email, pwd, tokens, is_admin) VALUES (%s, %s, %s, TRUE) RETURNING id",
                (ADMIN_EMAIL.strip(), pwd_hashed, 100)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            logger.info("Bootstrap admin user created: %s (id=%s)", ADMIN_EMAIL, new_id)
        except Exception as e:
            conn.rollback()
            logger.warning("Could not create bootstrap admin (user may already exist): %s", e)


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(ML_USER_TABLE_SQL)
            cur.execute(ML_MODEL_TABLE_SQL)
            try:
                cur.execute("ALTER TABLE ml_model ADD COLUMN IF NOT EXISTS feature_cols TEXT DEFAULT ''")
            except Exception as e:
                logger.warning(f"Could not add feature_cols column (may already exist): {e}")
            try:
                cur.execute("ALTER TABLE ml_user ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE")
            except Exception as e:
                logger.warning(f"Could not add is_admin column (may already exist): {e}")
        conn.commit()
        logger.info("Database initialized")
        _ensure_one_admin(conn)
        conn.commit()
    finally:
        return_connection(conn)


if __name__ == "__main__":
    init_db()
