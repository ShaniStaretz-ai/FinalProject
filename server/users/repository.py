import psycopg2
from psycopg2.extras import RealDictCursor
from server.db.connection import get_connection
from server.security.passwords import hash_password, verify_password


def create_user(email: str, password: str) -> bool:
    """Create a new user with 15 tokens. Returns True on success."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ml_user (email, pwd, tokens)
                VALUES (%s, %s, %s)
                """,
                (str(email), hash_password(password), 15)  # cast EmailStr → str
            )
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def validate_user(email: str, password: str) -> bool:
    """Validate email + password combination."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pwd FROM ml_user WHERE email=%s",
                (str(email),)
            )
            result = cur.fetchone()
            if not result:
                return False
            hashed_password = result[0]
            return verify_password(password, hashed_password)
    finally:
        conn.close()
