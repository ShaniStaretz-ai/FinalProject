from fastapi import HTTPException, Depends, APIRouter, status

from server.security.jwt_auth import create_jwt, get_current_user
from server.users.models import UserCreateRequest, UserLoginRequest, UserDeleteRequest
from server.users.repository import create_user, validate_user, delete_user, delete_user_by_id, get_user_tokens, get_user_id_by_email

router = APIRouter(
    prefix="/user",   # optional: adds /user to all endpoints
    tags=["users"]
)


# -----------------------------
# Endpoints
# -----------------------------
@router.post("/create")
async def user_create(payload: UserCreateRequest):
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
async def user_login(payload: UserLoginRequest):
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
async def user_delete(
    payload: UserDeleteRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Delete a user by ID. Requires valid authentication token.
    Users CANNOT delete their own account - they can only delete other users' accounts.
    """
    # Get the authenticated user's ID
    authenticated_user_id = get_user_id_by_email(current_user)
    if authenticated_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user not found"
        )
    
    # Prevent users from deleting their own account
    if payload.user_id == authenticated_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete your own account"
        )
    
    # Delete the requested user (must be different from authenticated user)
    success = delete_user_by_id(payload.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {payload.user_id} not found"
        )
    return {"status": "success", "message": f"User with ID {payload.user_id} deleted"}


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