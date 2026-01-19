from fastapi import HTTPException, Depends, APIRouter

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
    email = str(payload.email)
    success = create_user(email, payload.pwd)
    if not success:
        raise HTTPException(status_code=400, detail="User already exists or error creating user")
    token = create_jwt(email)
    return {"status": "success", "token": token}


@router.post("/login")
def user_login(payload: UserLoginRequest):
    email = str(payload.email)
    user = validate_user(email, payload.pwd)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_jwt(email)
    return {"status": "OK", "token": token}


@router.delete("/remove_user")
def user_delete(current_user: str = Depends(get_current_user)):
    success = delete_user(current_user)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "message": f"User {current_user} deleted"}


@router.get("/tokens/{username}")
def get_tokens(username: str, current_user: str = Depends(get_current_user)):
    if current_user != username:
        raise HTTPException(status_code=403, detail="Cannot access another user's tokens")
    tokens = get_user_tokens(username)
    if tokens is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": username, "tokens": tokens}


@router.get("/tokens/{username}")
def get_tokens(username: str, current_user: str = Depends(get_current_user)):
    # Only allow user to see their own tokens
    if current_user != username:
        raise HTTPException(status_code=403, detail="Cannot access another user's tokens")
    # Fetch tokens from DB
    tokens = get_user_tokens(username)
    return {"username": username, "tokens": tokens}