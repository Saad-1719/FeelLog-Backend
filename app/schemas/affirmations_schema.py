from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.services.db import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Affirmation(Base):
    __tablename__ = "affirmations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affirmations = Column(String, nullable=False)
    journal_id = Column(UUID(as_uuid=True), ForeignKey("journals.id"), nullable=False)
    journal = relationship("Journal", back_populates="affirmations")