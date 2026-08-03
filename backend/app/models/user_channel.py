from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class UserChannel(Base):
    __tablename__ = "user_channels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_type = Column(String(50), nullable=False) # e.g. "whatsapp", "telegram"
    phone_number = Column(String(50), nullable=True)
    status = Column(String(50), default="disconnected") # "connected", "disconnected", "connecting", etc
    account_id = Column(String(255), nullable=True) # The openclaw account id
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
