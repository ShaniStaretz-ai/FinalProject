import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from server.security.admin_auth import get_current_admin
from server.users.repository import (
    get_all_users,
    add_tokens_to_user,
    delete_user_by_id,
    update_user_password,
    get_user_id_by_email
)
from server.users.models import UserPasswordUpdateRequest, AddTokensRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


@router.get("/users")
async def list_users(
    min_tokens: Optional[int] = Query(None, description="Show users with at least X tokens"),
    current_admin: str = Depends(get_current_admin)
):
    """
    Get all users with optional token filter.
    Only accessible by admins.
    """
    logger.info(f"Admin {current_admin} requested user list (min_tokens={min_tokens})")
    users = get_all_users(min_tokens=min_tokens)
    return {
        "status": "success",
        "count": len(users),
        "users": users
    }


@router.post("/users/{user_id}/tokens")
async def add_tokens(
    user_id: int,
    payload: AddTokensRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Add tokens to a user's account.
    Requires email, credit_card (simulated), and amount in request body.
    Only accessible by admins.
    """
    email = str(payload.email)
    credit_card = payload.credit_card
    amount = payload.amount
    
    logger.info(f"Admin {current_admin} attempting to add {amount} tokens to user ID {user_id} (email: {email}, credit_card: {credit_card[:4] if len(credit_card) > 4 else '****'}****)")
    
    # Verify the email matches the user_id
    user_id_by_email = get_user_id_by_email(email)
    if user_id_by_email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found"
        )
    
    if user_id_by_email != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email {email} does not match user ID {user_id}"
        )
    
    success = add_tokens_to_user(email, amount)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add tokens"
        )
    
    logger.info(f"Admin {current_admin} successfully added {amount} tokens to {email}")
    return {
        "status": "success",
        "message": f"Added {amount} tokens to {email}",
        "email": email,
        "amount": amount
    }


@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: int,
    current_admin: str = Depends(get_current_admin)
):
    """
    Delete a user and all their trained models.
    Only accessible by admins.
    Admins cannot delete themselves.
    """
    logger.info(f"Admin {current_admin} attempting to delete user ID {user_id}")
    
    # Prevent admin from deleting themselves
    current_admin_id = get_user_id_by_email(current_admin)
    if current_admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )
    
    if current_admin_id == user_id:
        logger.warning(f"Admin {current_admin} attempted to delete their own account (ID: {user_id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete your own account"
        )
    
    success = delete_user_by_id(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    logger.info(f"Admin {current_admin} successfully deleted user ID {user_id}")
    return {
        "status": "success",
        "message": f"User with ID {user_id} and all associated models deleted"
    }


@router.post("/users/{user_id}/reset_password")
async def reset_user_password(
    user_id: int,
    payload: UserPasswordUpdateRequest,
    current_admin: str = Depends(get_current_admin)
):
    """
    Reset a user's password.
    Only accessible by admins.
    """
    email = str(payload.email)
    logger.info(f"Admin {current_admin} attempting to reset password for user ID {user_id} (email: {email})")
    
    # Verify the email matches the user_id
    user_id_by_email = get_user_id_by_email(email)
    if user_id_by_email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found"
        )
    
    if user_id_by_email != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email {email} does not match user ID {user_id}"
        )
    
    success = update_user_password(email, payload.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    logger.info(f"Admin {current_admin} successfully reset password for {email}")
    return {
        "status": "success",
        "message": f"Password reset successfully for {email}"
    }

