from pydantic import BaseModel, EmailStr, Field, field_validator
from bson import ObjectId
from typing import Optional

class UserBase(BaseModel):
    
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="User full name", min_length=3, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., description="User password", min_length=6, max_length=100)
    confirm_password: str = Field(..., description="User password", min_length=6, max_length=100)
    @field_validator("confirm_password")
    def check_password(cls, confirmPassword, values):
        if "password" in values and confirmPassword != values["password"]:
            raise ValueError("Passwords do not match")
        return confirmPassword
       
    
class UserInDB(UserBase):
    id: int = Field(...,alias='_id' ,description="User ID")
    hashed_password: str
    
    class Config:
        arbitray_types_allowed = True
        json_encoders = {ObjectId: str}

class UserResponse(UserBase):
    id: int 

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=6, max_length=100)