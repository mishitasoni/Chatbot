from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    platform = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete"
    )