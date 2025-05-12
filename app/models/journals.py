from pydantic import BaseModel, Field,ConfigDict
from typing import Optional, Any, List
from datetime import datetime
from uuid import UUID


class JournalBase(BaseModel):
    title: str = Field(..., description="Journal title", min_length=1)
    content: str = Field(..., description="Journal content", min_length=1)
    created_at: Optional[datetime] = Field(None, description="Journal creation date")
    updated_at: Optional[datetime] = Field(None, description="Journal update date")


class JournalReponse(BaseModel):
    title: str
    content: str
    sentiment_label: str
    sentiment_probability: float
    output: Optional[Any] = None


class AffirmationsRead(BaseModel):
    id: UUID
    affirmations: List[str]

    # journal_id:UUID
    model_config = ConfigDict(from_attributes=True)


class AllJournalsAndAffirmations(BaseModel):
    content: str
    sentiment_label: str
    created_at: datetime
    title: str
    id: UUID
    sentiment_score: float
    affirmations: List[AffirmationsRead] = []  # Include affirmations here

    model_config = ConfigDict(from_attributes=True)
