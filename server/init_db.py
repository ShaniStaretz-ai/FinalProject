import logging
from server.db.connection import get_connection
from server.db.schema import ML_USER_TABLE_SQL, ML_MODEL_TABLE_SQL

logger = logging.getLogger(__name__)


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(ML_USER_TABLE_SQL)
            cur.execute(ML_MODEL_TABLE_SQL)
            
            # Add feature_cols column if it doesn't exist (migration)
            try:
                cur.execute("ALTER TABLE ml_model ADD COLUMN IF NOT EXISTS feature_cols TEXT DEFAULT ''")
            except Exception as e:
                logger.warning(f"Could not add feature_cols column (may already exist): {e}")
            
        conn.commit()
        logger.info("Database initialized")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
