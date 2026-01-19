from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from server.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_MINUTES

# -----------------------------
# Security scheme for FastAPI / Swagger
# -----------------------------
bearer_scheme = HTTPBearer()  # Shows "Authorize" button in Swagger

# -----------------------------
# JWT helpers
# -----------------------------
def create_jwt(email: str, expires_minutes: int = JWT_EXP_MINUTES) -> str:
    """
    Create a JWT token for a given email with expiration.
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": email, "exp": expire}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_jwt(token: str) -> str:
    """
    Decode a JWT token and return the email (sub claim).
    Raises HTTPException if invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# -----------------------------
# Dependency for protected endpoints
# -----------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    """
    Use as: current_user: str = Depends(get_current_user)
    Swagger will automatically prompt for the Bearer token.
    """
    token = credentials.credentials
    return decode_jwt(token)
