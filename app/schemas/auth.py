from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="User full name", min_length=3, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., description="User password", min_length=8, max_length=100)
    confirm_password: str = Field(..., description="Confirm password", min_length=8, max_length=100)
    
    @field_validator("confirm_password")
    def check_password(cls, confirm_password: str, info: ValidationInfo) -> str:
        values = info.data
        if "password" in values and confirm_password != values["password"]:
            raise ValueError("Passwords do not match")
        return confirm_password

class UserInDB(UserBase):
    id: UUID = Field(default_factory=uuid4, description="User ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hashed_password: str = Field(..., description="Hashed password")
    is_active: bool = Field(default=True, description="Is user active")
    
    class Config:
        from_attributes = True  # Enable ORM mode

class UserPublic(UserBase):
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=8)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    type: Optional[str] = None