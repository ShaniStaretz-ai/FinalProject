from psycopg2.pool import ThreadedConnectionPool

from server.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

_pool: ThreadedConnectionPool | None = None
_MIN_CONN = 1
_MAX_CONN = 10


def get_connection():
    global _pool
    if _pool is None:
        if not DB_NAME or not DB_USER:
            raise RuntimeError("Missing DB_NAME or DB_USER. Set DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD in .env")
        _pool = ThreadedConnectionPool(
            _MIN_CONN,
            _MAX_CONN,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    return _pool.getconn()


def return_connection(conn):
    global _pool
    if _pool is not None and conn is not None:
        try:
            _pool.putconn(conn)
        except Exception:
            pass
