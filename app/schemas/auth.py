from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="User full name", min_length=3, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., description="User password", min_length=6, max_length=100)
    confirm_password: str = Field(..., description="Confirm password", min_length=6, max_length=100)
    
    @field_validator("confirm_password")
    def check_password(cls, confirm_password: str, info: ValidationInfo) -> str:
        values = info.data
        if "password" in values and confirm_password != values["password"]:
            raise ValueError("Passwords do not match")
        return confirm_password

class UserPublic(UserBase):
    id: UUID
    created_at:datetime
    profile_photo: str  # Add profile photo field
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    type: Optional[str] = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")