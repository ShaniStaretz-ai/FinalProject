import logging
from server.db.connection import get_connection
from server.db.schema import ML_USER_TABLE_SQL

logger = logging.getLogger(__name__)


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(ML_USER_TABLE_SQL)
        conn.commit()
        logger.info("Database initialized")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
