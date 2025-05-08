from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.services.db import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Journal(Base):
    __tablename__ = "journals"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sentiment_label = Column(String, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    user = relationship("User", back_populates="journals")
    affirmations = relationship(
        "Affirmation", back_populates="journal", cascade="all, delete-orphan"
    )
