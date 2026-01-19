"""
Repository functions for model management.
"""
from typing import Optional, List, Dict
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

from server.db.connection import get_connection

logger = logging.getLogger(__name__)


def create_model_record(user_id: int, model_name: str, model_type: str, file_path: str) -> Optional[int]:
    """
    Create a model record in the database.
    Returns the model ID on success, None on error.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ml_model (user_id, model_name, model_type, file_path) VALUES (%s, %s, %s, %s) RETURNING id",
                    (user_id, model_name, model_type, file_path)
                )
                model_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"Model record created: {model_name} (user {user_id})")
                return model_id
        except psycopg2.IntegrityError as e:
            conn.rollback()
            logger.warning(f"Model name {model_name} already exists for user {user_id}")
            return None
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating model record: {e}")
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error creating model record: {e}")
        return None


def get_user_models(user_id: int) -> List[Dict]:
    """
    Get all models for a specific user.
    Returns list of model dictionaries.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, model_name, model_type, file_path, created_at FROM ml_model WHERE user_id=%s ORDER BY created_at DESC",
                    (user_id,)
                )
                models = cur.fetchall()
                return [dict(model) for model in models]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error fetching models for user {user_id}: {e}")
        return []


def get_model_by_name(user_id: int, model_name: str) -> Optional[Dict]:
    """
    Get a specific model by name for a user.
    Returns model dict or None if not found.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, model_name, model_type, file_path, created_at FROM ml_model WHERE user_id=%s AND model_name=%s",
                    (user_id, model_name)
                )
                model = cur.fetchone()
                return dict(model) if model else None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error fetching model {model_name} for user {user_id}: {e}")
        return None


def delete_model(user_id: int, model_name: str) -> bool:
    """
    Delete a model record for a user.
    Returns True if deleted, False if not found.
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM ml_model WHERE user_id=%s AND model_name=%s RETURNING id",
                    (user_id, model_name)
                )
                deleted = cur.rowcount
                conn.commit()
                return deleted > 0
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error deleting model {model_name} for user {user_id}: {e}")
        return False

