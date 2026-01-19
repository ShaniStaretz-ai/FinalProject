from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    email: EmailStr
    pwd: str = Field(min_length=4, max_length=72)


class UserLoginRequest(BaseModel):
    email: EmailStr
    pwd: str
