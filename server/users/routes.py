from fastapi import HTTPException, Depends, APIRouter, status

from server.security.jwt_auth import create_jwt, get_current_user
from server.users.models import UserCreateRequest, UserLoginRequest
from server.users.repository import create_user, validate_user, delete_user, get_user_tokens

router = APIRouter(
    prefix="/user",   # optional: adds /user to all endpoints
    tags=["users"]
)


# -----------------------------
# Endpoints
# -----------------------------
@router.post("/create")
def user_create(payload: UserCreateRequest):
    """
    Create a new user account.
    User must log in separately after account creation.
    """
    email = str(payload.email)
    success = create_user(email, payload.pwd)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists or error creating user"
        )
    return {
        "status": "success",
        "message": "User created successfully. Please log in to get an access token.",
        "email": email
    }


@router.post("/login")
def user_login(payload: UserLoginRequest):
    """
    Login endpoint. Accepts email and password, returns JWT token.
    """
    email = str(payload.email)
    user = validate_user(email, payload.pwd)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_jwt(email)
    return {
        "status": "OK",
        "access_token": token,
        "token_type": "bearer"
    }


@router.delete("/remove_user")
async def user_delete(current_user: str = Depends(get_current_user)):
    """
    Delete the current authenticated user.
    """
    success = delete_user(current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"status": "success", "message": f"User {current_user} deleted"}


@router.get("/tokens")
async def get_tokens(current_user: str = Depends(get_current_user)):
    """
    Get current user's tokens. 
    Requires authentication token in header (Authorization: Bearer <token>).
    Returns tokens for the authenticated user only.
    """
    tokens = get_user_tokens(current_user)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"username": current_user, "tokens": tokens}