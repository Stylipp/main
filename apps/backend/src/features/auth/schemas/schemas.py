from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str | None = None
    onboarding_completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Keep TokenResponse for backward compatibility if referenced elsewhere
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
