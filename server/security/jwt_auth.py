import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from server.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_MINUTES

logger = logging.getLogger(__name__)

# -----------------------------
# HTTPBearer for FastAPI / Swagger - allows direct token input
# -----------------------------
bearer_scheme = HTTPBearer(auto_error=False)

# -----------------------------
# JWT helpers using PyJWT
# -----------------------------
def create_jwt(email: str, expires_minutes: int = JWT_EXP_MINUTES) -> str:
    """
    Create a JWT token for a given email with expiration using PyJWT.
    PyJWT automatically handles exp and iat as datetime objects or timestamps.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)
    payload = {
        "sub": email,
        "exp": expire,  # PyJWT will convert datetime to timestamp
        "iat": now
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.debug(f"JWT token created for: {email} (expires in {expires_minutes} minutes)")
    return token

def decode_jwt(token: str) -> str:
    """
    Decode a JWT token and return the email (sub claim).
    Raises HTTPException if invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            logger.warning("JWT token validation failed: missing subject")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
        logger.debug(f"JWT token validated for: {email}")
        return email
    except ExpiredSignatureError:
        logger.warning("JWT token validation failed: token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except InvalidTokenError as e:
        logger.warning(f"JWT token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"JWT token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation error: {str(e)}"
        )

# -----------------------------
# Dependency for protected endpoints using HTTPBearer
# -----------------------------
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """
    Use as: current_user: str = Depends(get_current_user)
    Swagger will show a simple "Authorize" button where you can paste your token.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    return decode_jwt(token)
