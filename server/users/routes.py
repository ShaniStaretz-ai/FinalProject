from fastapi import APIRouter,  HTTPException
from server.users.models import UserCreateRequest, UserLoginRequest
from server.users.repository import create_user, validate_user

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/create")
def user_create(payload: UserCreateRequest):
    """Create a new user with 15 tokens."""
    try:
        success = create_user(str(payload.email), payload.pwd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")

    if not success:
        raise HTTPException(status_code=400, detail="User already exists")

    return {"status": "OK"}


@router.post("/login")
def user_login(payload: UserLoginRequest):
    valid = validate_user(payload.email, payload.pwd)
    return "OK" if valid else "FAIL"
