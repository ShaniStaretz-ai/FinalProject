from typing import Optional
import logging
from psycopg2.extras import RealDictCursor

from server.security.passwords import hash_password, verify_password
from server.db.connection import get_connection

logger = logging.getLogger(__name__)

# ----------------------------
# User management
# ----------------------------
def create_user(email: str, pwd: str, tokens: int = 15) -> bool:
    """
    Create a new user with hashed password and initial tokens.
    Returns True on success, False if user already exists or error occurs.
    """
    import psycopg2
    try:
        pwd_hashed = hash_password(pwd)  # centralized helper
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ml_user (email, pwd, tokens) VALUES (%s, %s, %s) RETURNING id",
                    (email, pwd_hashed, tokens)
                )
                new_id = cur.fetchone()[0]
                conn.commit()  # Explicitly commit the transaction
                logger.info(f"Created user {email} with ID {new_id}")
            return True
        except psycopg2.IntegrityError as e:
            # User already exists (unique constraint violation)
            conn.rollback()
            logger.warning(f"User {email} already exists")
            return False
        except Exception as e:
            conn.rollback()  # Rollback on error
            raise
        finally:
            conn.close()
    except ValueError as e:
        # Password validation error
        logger.error(f"Password validation error for {email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating user {email}: {e}")
        return False

def validate_user(email: str, pwd: str) -> Optional[dict]:
    """
    Validate user credentials. Returns user dict if valid, else None.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM ml_user WHERE email=%s", (email,))
                user = cur.fetchone()
        finally:
            conn.close()
        
        if not user:
            logger.warning(f"User not found: {email}")
            return None
            
        if verify_password(pwd, user["pwd"]):  # centralized helper
            logger.info(f"User {email} authenticated successfully")
            return user
        else:
            logger.warning(f"Password verification failed for user: {email}")
            return None
    except Exception as e:
        logger.error(f"Error validating user {email}: {e}")
        return None

def delete_user(email: str) -> bool:
    """
    Delete user by email. Returns True if deleted, False if not found.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ml_user WHERE email=%s RETURNING id", (email,))
                deleted = cur.rowcount
                conn.commit()  # Explicitly commit the transaction
                return deleted > 0
        except Exception as e:
            conn.rollback()  # Rollback on error
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error deleting user {email}: {e}")
        return False

def delete_user_by_id(user_id: int) -> bool:
    """
    Delete user by ID. Returns True if deleted, False if not found.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ml_user WHERE id=%s RETURNING email", (user_id,))
                result = cur.fetchone()
                deleted = cur.rowcount
                conn.commit()  # Explicitly commit the transaction
                if deleted > 0 and result:
                    logger.info(f"Deleted user with ID {user_id} (email: {result[0]})")
                return deleted > 0
        except Exception as e:
            conn.rollback()  # Rollback on error
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error deleting user with ID {user_id}: {e}")
        return False

def get_user_id_by_email(email: str) -> Optional[int]:
    """
    Get user ID by email. Returns int or None if user not found.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM ml_user WHERE email=%s", (email,))
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error fetching user ID for {email}: {e}")
        return None

def get_user_tokens(email: str) -> Optional[int]:
    """
    Get the number of tokens a user has.
    Returns int or None if user not found.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT tokens FROM ml_user WHERE email=%s", (email,))
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error fetching tokens for {email}: {e}")
        return None

def update_user_tokens(email: str, new_tokens: int) -> bool:
    """
    Update a user's token count. Returns True if updated, False otherwise.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ml_user SET tokens=%s WHERE email=%s RETURNING id",
                    (new_tokens, email)
                )
                updated = cur.rowcount
                conn.commit()  # Explicitly commit the transaction
                return updated > 0
        except Exception as e:
            conn.rollback()  # Rollback on error
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error updating tokens for {email}: {e}")
        return False
