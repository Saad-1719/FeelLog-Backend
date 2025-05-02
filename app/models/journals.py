from pydantic import BaseModel, Field
from bson import ObjectId

from typing import Optional

from datetime import datetime

class JournalBase(BaseModel):
    title: str = Field(..., description="Journal title", min_length=1)
    content: str = Field(..., description="Journal content", min_length=1)
    created_at: Optional[datetime] = Field(None, description="Journal creation date")
    updated_at: Optional[datetime] = Field(None, description="Journal update date")


class JournalCreate(JournalBase):
    pass

class JournalInDB(JournalBase):
    id: int = Field(..., description="Journal ID")
    user_id: str = Field(..., description="User ID of the journal owner")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "title": "My First Journal",
                "content": "This is the content of my first journal.",
                "created_at": "2023-10-01T12:00:00Z",
                "updated_at": "2023-10-01T12:00:00Z",
                "user_id": "603d2f4f1c4ae5b8d8e4a0b0"
            }
        }
