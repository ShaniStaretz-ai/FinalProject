from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    email: EmailStr
    pwd: str = Field(min_length=4, max_length=72)


class UserLoginRequest(BaseModel):
    email: EmailStr
    pwd: str

class TokenInfoRequest(BaseModel):
    username: str
    credit_card: str
    amount: int

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserDeleteRequest(BaseModel):
    user_id: int

class UserPasswordUpdateRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=4, max_length=72)