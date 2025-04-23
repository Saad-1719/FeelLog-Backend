from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from datetime import datetime, timezone
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="User full name", min_length=3, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., description="User password", min_length=6, max_length=100)
    confirm_password: str = Field(..., description="Confirm password", min_length=6, max_length=100)

    @field_validator("confirm_password")
    def check_password(cls, confirm_password: str, info: "ValidationInfo") -> str:
        values = info.data  # Access the data dictionary from ValidationInfo
        if "password" in values and confirm_password != values["password"]:
            raise ValueError("Passwords do not match")
        return confirm_password

class UserInDB(UserBase):
    id: int
    created_at: datetime
    hashed_password: str
    is_active: bool

    class Config:
        from_attributes = True  # Enable ORM mode

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=6)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    type: Optional[str] = None