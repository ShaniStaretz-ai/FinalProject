"""
Repository functions for model management.
"""
from typing import Optional, List, Dict
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

from server.db.connection import get_connection

logger = logging.getLogger(__name__)


def create_model_record(user_id: int, model_name: str, model_type: str, file_path: str, feature_cols: str) -> Optional[int]:
    """
    Create a model record in the database.
    Returns the model ID on success, None on error.
    
    Args:
        user_id: User ID who owns the model
        model_name: Name of the model
        model_type: Type of model (e.g., "linear", "knn")
        file_path: Full path to the model file
        feature_cols: JSON string of feature columns used for training
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ml_model (user_id, model_name, model_type, file_path, feature_cols) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (user_id, model_name, model_type, file_path, feature_cols)
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
                    "SELECT id, model_name, model_type, file_path, feature_cols, created_at FROM ml_model WHERE user_id=%s ORDER BY created_at DESC",
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
                    "SELECT id, model_name, model_type, file_path, feature_cols, created_at FROM ml_model WHERE user_id=%s AND model_name=%s",
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
    Delete a model record for a user and its associated files from disk.
    Returns True if deleted, False if not found.
    """
    import os
    from server.config import METRICS_DIR
    
    try:
        # First, get the model record to find the file path
        model_record = get_model_by_name(user_id, model_name)
        if model_record is None:
            return False
        
        # Delete model file from disk
        file_path = model_record.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted model file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete model file {file_path}: {e}")
        
        # Delete metrics file from disk
        metrics_path = os.path.join(METRICS_DIR, f"{model_name}_metrics.json")
        if os.path.exists(metrics_path):
            try:
                os.remove(metrics_path)
                logger.info(f"Deleted metrics file: {metrics_path}")
            except Exception as e:
                logger.warning(f"Failed to delete metrics file {metrics_path}: {e}")
        
        # Now delete the database record
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

