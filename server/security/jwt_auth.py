from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from server.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_MINUTES

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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
        return email
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
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
