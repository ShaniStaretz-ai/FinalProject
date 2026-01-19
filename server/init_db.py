from db.connection import get_connection
from db.schema import ML_USER_TABLE_SQL


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(ML_USER_TABLE_SQL)
        conn.commit()
        print("Database initialized")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
