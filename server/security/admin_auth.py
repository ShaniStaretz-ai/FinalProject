import logging
from fastapi import HTTPException, status, Depends
from server.security.jwt_auth import get_current_user
from server.users.repository import is_user_admin

logger = logging.getLogger(__name__)


def get_current_admin(current_user: str = Depends(get_current_user)) -> str:
    if not is_user_admin(current_user):
        logger.warning(f"Admin access denied for user: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    logger.debug(f"Admin access granted for: {current_user}")
    return current_user
