import uuid

from pydantic import BaseModel, EmailStr, Field

from backend.app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    nickname: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(ORMModel):
    id: uuid.UUID
    email: EmailStr
    nickname: str | None = None
    avatar_url: str | None = None

