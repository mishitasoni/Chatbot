from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.schemas.message import MessageResponse

class ConversationBase(BaseModel):
    platform: str

class ConversationCreate(ConversationBase):
    user_id: int

class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    messages: Optional[List[MessageResponse]] = []

    class Config:
        from_attributes = True