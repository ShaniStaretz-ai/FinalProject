import bcrypt
import logging

logger = logging.getLogger(__name__)


def _truncate_to_bytes(password: str, max_bytes: int = 72) -> bytes:
    if isinstance(password, bytes):
        password_bytes = password
    else:
        password_bytes = password.encode('utf-8')
    if len(password_bytes) <= max_bytes:
        return password_bytes
    truncated_bytes = password_bytes[:max_bytes]
    while truncated_bytes and (truncated_bytes[-1] & 0x80) and not (truncated_bytes[-1] & 0x40):
        truncated_bytes = truncated_bytes[:-1]
    return truncated_bytes


def hash_password(plain_password: str) -> str:
    if len(plain_password) < 4:
        raise ValueError("Password must be at least 4 characters")
    password_bytes = _truncate_to_bytes(plain_password, max_bytes=72)
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise ValueError(f"Failed to hash password: {e}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if not plain_password or not hashed_password:
            logger.warning("Password verification: empty password or hash")
            return False
        if not hashed_password.startswith('$2'):
            logger.warning("Password verification: invalid hash format (doesn't start with $2)")
            return False
        password_bytes = _truncate_to_bytes(plain_password, max_bytes=72)
        hashed_bytes = hashed_password.encode('utf-8')
        result = bcrypt.checkpw(password_bytes, hashed_bytes)
        if not result:
            logger.debug("Password verification failed: bcrypt.checkpw returned False")
        return result
    except Exception as e:
        logger.error(f"Password verification error: {e}", exc_info=True)
        return False
