from typing import Optional
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, status

from server.security.passwords import hash_password, verify_password
from server.db.connection import get_connection, return_connection

logger = logging.getLogger(__name__)


def create_user(email: str, pwd: str, tokens: int = 15, is_admin: bool = False) -> bool:
    try:
        pwd_hashed = hash_password(pwd)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ml_user (email, pwd, tokens, is_admin) VALUES (%s, %s, %s, %s) RETURNING id",
                    (email, pwd_hashed, tokens, is_admin)
                )
                new_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"Created user {email} with ID {new_id}")
            return True
        except psycopg2.IntegrityError:
            conn.rollback()
            logger.warning(f"User {email} already exists")
            return False
        except Exception as e:
            conn.rollback()
            raise
        finally:
            return_connection(conn)
    except ValueError as e:
        logger.error(f"Password validation error for {email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating user {email}: {e}")
        return False

def validate_user(email: str, pwd: str) -> Optional[dict]:
    try:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM ml_user WHERE email=%s", (email,))
                user = cur.fetchone()
        finally:
            return_connection(conn)

        if not user:
            logger.warning(f"User not found: {email}")
            return None
        stored_hash = user["pwd"]
        if not stored_hash or len(stored_hash) < 10:
            logger.error(f"Invalid password hash stored for user {email}: hash too short or empty")
            return None
        
        if not stored_hash.startswith('$2'):
            logger.error(f"Invalid password hash format for user {email}: hash doesn't start with $2 (got: {stored_hash[:10]}...)")
            return None
        
        if verify_password(pwd, stored_hash):
            logger.info(f"User {email} authenticated successfully")
            return user
        else:
            logger.warning(f"Password verification failed for user: {email} (hash format looks valid: {stored_hash[:20]}...)")
            return None
    except Exception as e:
        logger.error(f"Error validating user {email}: {e}")
        return None

def delete_user(email: str) -> bool:
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ml_user WHERE email=%s RETURNING id", (email,))
                deleted = cur.rowcount
                conn.commit()
                return deleted > 0
        except Exception as e:
            conn.rollback()
            raise
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error deleting user {email}: {e}")
        return False


def delete_user_by_id(user_id: int) -> bool:
    import os
    from server.models.repository import get_user_models
    try:
        models = get_user_models(user_id)
        deleted_files = 0
        
        for model in models:
            file_path = model.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files += 1
                    logger.info(f"Deleted model file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete model file {file_path}: {e}")
            model_name = model.get("model_name")
            if model_name:
                from server.config import METRICS_DIR
                metrics_path = os.path.join(METRICS_DIR, f"{model_name}_metrics.json")
                if os.path.exists(metrics_path):
                    try:
                        os.remove(metrics_path)
                        logger.info(f"Deleted metrics file: {metrics_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete metrics file {metrics_path}: {e}")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ml_user WHERE id=%s RETURNING email", (user_id,))
                result = cur.fetchone()
                deleted = cur.rowcount
                conn.commit()
                if deleted > 0 and result:
                    logger.info(f"Deleted user with ID {user_id} (email: {result[0]}), removed {deleted_files} model file(s)")
                return deleted > 0
        except Exception as e:
            conn.rollback()
            raise
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error deleting user with ID {user_id}: {e}")
        return False


def get_user_id_by_email(email: str) -> Optional[int]:
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM ml_user WHERE email=%s", (email,))
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error fetching user ID for {email}: {e}")
        return None


def get_user_tokens(email: str) -> Optional[int]:
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT tokens FROM ml_user WHERE email=%s", (email,))
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error fetching tokens for {email}: {e}")
        return None


def update_user_password(email: str, new_password: str) -> bool:
    try:
        pwd_hashed = hash_password(new_password)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ml_user SET pwd=%s WHERE email=%s RETURNING id",
                    (pwd_hashed, email)
                )
                updated = cur.rowcount
                conn.commit()
                if updated > 0:
                    logger.info(f"Password updated for user: {email}")
                    return True
                return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating password for {email}: {e}")
            raise
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error updating password for {email}: {e}")
        return False


def update_user_tokens(email: str, new_tokens: int) -> bool:
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ml_user SET tokens=%s WHERE email=%s RETURNING id",
                    (new_tokens, email)
                )
                updated = cur.rowcount
                conn.commit()
                return updated > 0
        except Exception as e:
            conn.rollback()
            raise
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error updating tokens for {email}: {e}")
        return False


def refund_tokens(email: str, amount: int) -> bool:
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ml_user SET tokens = tokens + %s WHERE email = %s RETURNING id",
                    (amount, email)
                )
                updated = cur.rowcount
                conn.commit()
                return updated > 0
        except Exception as e:
            conn.rollback()
            raise
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error refunding tokens for {email}: {e}")
        return False


def check_and_deduct_tokens(email: str, required_tokens: int) -> bool:
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ml_user SET tokens = tokens - %s WHERE email = %s AND tokens >= %s RETURNING id, tokens",
                    (required_tokens, email, required_tokens)
                )
                row = cur.fetchone()
                conn.commit()
                if row is None:
                    current = get_user_tokens(email)
                    if current is None:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=f"Insufficient tokens. Required: {required_tokens}, Available: {current}"
                    )
                logger.info(f"User {email}: Deducted {required_tokens} tokens. Remaining: {row[1]}")
                return True
        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Token deduction failed for {email}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update tokens")
        finally:
            return_connection(conn)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in check_and_deduct_tokens for {email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update tokens")


def is_user_admin(email: str) -> bool:
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT is_admin FROM ml_user WHERE email=%s", (email,))
                row = cur.fetchone()
                if row:
                    return bool(row[0])
                return False
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error checking admin status for {email}: {e}")
        return False


def get_all_users(min_tokens: Optional[int] = None) -> list:
    try:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if min_tokens is not None:
                    cur.execute(
                        "SELECT id, email, tokens, is_admin FROM ml_user WHERE tokens >= %s ORDER BY id",
                        (min_tokens,)
                    )
                else:
                    cur.execute("SELECT id, email, tokens, is_admin FROM ml_user ORDER BY id")
                users = cur.fetchall()
                return [dict(user) for user in users]
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        return []


def add_tokens_to_user(email: str, amount: int) -> bool:
    """Add tokens atomically (tokens = tokens + amount in a single UPDATE)."""
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ml_user SET tokens = tokens + %s WHERE email = %s RETURNING id, tokens",
                    (amount, email)
                )
                row = cur.fetchone()
                conn.commit()
                if row is None:
                    logger.warning(f"User not found: {email}")
                    return False
                logger.info(f"Added {amount} tokens to {email}. New balance: {row[1]}")
                return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding tokens to {email}: {e}")
            raise
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error adding tokens to {email}: {e}")
        return False
