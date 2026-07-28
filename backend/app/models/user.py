from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(255), unique=True, nullable=True)

    phone = Column(String(20), unique=True, nullable=True)

    telegram_bot_token = Column(String(255), nullable=True)
    whatsapp_session_data = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())