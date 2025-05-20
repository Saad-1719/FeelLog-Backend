import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.services.db import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    session_id = Column(
        String, nullable=True, unique=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    user = relationship("User", back_populates="refresh_tokens")
