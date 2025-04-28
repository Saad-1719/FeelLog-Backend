import uuid
from sqlalchemy import Column,String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.services.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    profile_photo=Column(String,nullable=True) #new column added
    refresh_token=Column(String,nullable=True)
    refresh_token_expires_at = Column(DateTime, nullable=True)  # Optional: store expiry
