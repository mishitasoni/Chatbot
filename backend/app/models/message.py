from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    conversation_id = Column(Integer, ForeignKey("conversations.id"))

    sender = Column(String)

    message = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )