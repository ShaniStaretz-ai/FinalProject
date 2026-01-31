from typing import Optional, List, Dict
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

from server.db.connection import get_connection, return_connection

logger = logging.getLogger(__name__)


def create_model_record(user_id: int, model_name: str, model_type: str, file_path: str, feature_cols: str) -> Optional[int]:
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
        except psycopg2.IntegrityError:
            conn.rollback()
            logger.warning(f"Model name {model_name} already exists for user {user_id}")
            return None
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating model record: {e}")
            raise
        finally:
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error creating model record: {e}")
        return None


def get_user_models(user_id: int) -> List[Dict]:
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
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error fetching models for user {user_id}: {e}")
        return []


def get_model_by_name(user_id: int, model_name: str) -> Optional[Dict]:
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
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error fetching model {model_name} for user {user_id}: {e}")
        return None


def delete_model(user_id: int, model_name: str) -> bool:
    import os
    from server.config import METRICS_DIR
    
    try:
        model_record = get_model_by_name(user_id, model_name)
        if model_record is None:
            return False
        file_path = model_record.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted model file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete model file {file_path}: {e}")
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
            return_connection(conn)
    except Exception as e:
        logger.error(f"Error deleting model {model_name} for user {user_id}: {e}")
        return False

