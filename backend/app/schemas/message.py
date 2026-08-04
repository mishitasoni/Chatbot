from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    message: str

class MessageCreate(MessageBase):
    conversation_id: int
    sender: str = "user"
    platform: str = "general"

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    sender: str
    created_at: datetime

    class Config:
        from_attributes = True