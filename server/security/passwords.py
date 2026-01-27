import bcrypt
import logging

logger = logging.getLogger(__name__)


def _truncate_to_bytes(password: str, max_bytes: int = 72) -> bytes:
    """
    Truncate password to max_bytes as bytes, handling UTF-8 encoding properly.
    Bcrypt has a 72-byte limit, so we need to ensure passwords don't exceed this.
    Returns bytes for direct use with bcrypt.
    """
    if isinstance(password, bytes):
        password_bytes = password
    else:
        password_bytes = password.encode('utf-8')
    
    if len(password_bytes) <= max_bytes:
        return password_bytes
    
    # Truncate to max_bytes
    truncated_bytes = password_bytes[:max_bytes]
    
    # Remove any incomplete UTF-8 sequences at the end
    # UTF-8 continuation bytes start with 10xxxxxx (0x80-0xBF)
    # UTF-8 start bytes start with 11xxxxxx (0xC0-0xFF) or 0xxxxxxx (0x00-0x7F)
    while truncated_bytes and (truncated_bytes[-1] & 0x80) and not (truncated_bytes[-1] & 0x40):
        truncated_bytes = truncated_bytes[:-1]
    
    return truncated_bytes


def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt directly.
    Automatically handles the 72-byte limit by truncating to 72 bytes.
    """
    if len(plain_password) < 4:
        raise ValueError("Password must be at least 4 characters")
    
    # Truncate to 72 bytes to comply with bcrypt limit
    # Bcrypt works with bytes, so we truncate the bytes representation
    password_bytes = _truncate_to_bytes(plain_password, max_bytes=72)
    
    try:
        # Generate salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Return as string (bcrypt hash is ASCII-safe)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise ValueError(f"Failed to hash password: {e}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    Uses the same truncation logic as hash_password for consistency.
    """
    try:
        # Validate inputs
        if not plain_password or not hashed_password:
            logger.warning("Password verification: empty password or hash")
            return False
        
        # Check if hash looks valid (bcrypt hashes start with $2a$, $2b$, or $2y$)
        if not hashed_password.startswith('$2'):
            logger.warning(f"Password verification: invalid hash format (doesn't start with $2)")
            return False
        
        # Truncate to 72 bytes to match hash_password behavior
        password_bytes = _truncate_to_bytes(plain_password, max_bytes=72)
        hashed_bytes = hashed_password.encode('utf-8')
        result = bcrypt.checkpw(password_bytes, hashed_bytes)
        
        if not result:
            logger.debug(f"Password verification failed: bcrypt.checkpw returned False")
        
        return result
    except Exception as e:
        logger.error(f"Password verification error: {e}", exc_info=True)
        return False
