import logging

from fastapi import HTTPException, Depends, APIRouter, status

from server.security.jwt_auth import create_jwt, get_current_user
from server.users.models import UserCreateRequest, UserLoginRequest, UserDeleteRequest, UserPasswordUpdateRequest
from server.users.repository import create_user, validate_user, delete_user, delete_user_by_id, get_user_tokens, get_user_id_by_email, update_user_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["users"])


@router.post("/create")
async def user_create(payload: UserCreateRequest):
    email = str(payload.email)
    logger.info(f"User creation attempt: {email}")
    success = create_user(email, payload.pwd)
    if not success:
        logger.warning(f"User creation failed: {email} (already exists or error)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists or error creating user"
        )
    logger.info(f"User created successfully: {email}")
    return {
        "status": "success",
        "message": "User created successfully. Please log in to get an access token.",
        "email": email
    }


@router.post("/login")
async def user_login(payload: UserLoginRequest):
    email = str(payload.email)
    logger.info(f"Login attempt: {email}")
    user = validate_user(email, payload.pwd)
    if not user:
        logger.warning(f"Login failed: {email} (invalid credentials)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_jwt(email)
    logger.info(f"Login successful: {email}")
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
    authenticated_user_id = get_user_id_by_email(current_user)
    if authenticated_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user not found"
        )
    if payload.user_id == authenticated_user_id:
        logger.warning(f"User deletion blocked: {current_user} attempted to delete own account (ID: {payload.user_id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete your own account"
        )
    
    logger.info(f"User deletion request: {current_user} (ID: {authenticated_user_id}) attempting to delete user ID {payload.user_id}")
    success = delete_user_by_id(payload.user_id)
    if not success:
        logger.warning(f"User deletion failed: User ID {payload.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {payload.user_id} not found"
        )
    logger.info(f"User deleted successfully: ID {payload.user_id} by {current_user}")
    return {"status": "success", "message": f"User with ID {payload.user_id} deleted"}


@router.get("/tokens")
async def get_tokens(current_user: str = Depends(get_current_user)):
    tokens = get_user_tokens(current_user)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"username": current_user, "tokens": tokens}


@router.post("/reset_password")
async def reset_password(
    payload: UserPasswordUpdateRequest,
    current_user: str = Depends(get_current_user)
):
    email = str(payload.email)
    if email.lower() != current_user.lower():
        logger.warning(f"Password reset denied: {current_user} attempted to reset password for {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reset your own password. Email must match your account."
        )
    logger.info(f"Password reset attempt for: {email}")
    user_id = get_user_id_by_email(current_user)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    success = update_user_password(email, payload.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    logger.info(f"Password reset successful for: {email}")
    return {
        "status": "success",
        "message": "Password updated successfully. Please log in with your new password."
    }