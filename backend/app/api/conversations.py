from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List

from app.database.dependencies import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import ConversationResponse
from app.schemas.message import MessageResponse, MessageCreate
from app.api.ws import manager
from app.services.chatbot import ask_llm

router = APIRouter()

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(platform: str, x_user_id: int = Header(...), db: Session = Depends(get_db)):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == x_user_id,
        Conversation.platform.like(f"{platform}%")
    ).order_by(Conversation.id.desc()).all()
    return conversations

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(conversation_id: int, x_user_id: int = Header(...), db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation.messages

@router.post("/chat", response_model=MessageResponse)
async def send_chat_message(msg_in: MessageCreate, x_user_id: int = Header(...), db: Session = Depends(get_db)):
    # Verify conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == msg_in.conversation_id,
        Conversation.user_id == x_user_id
    ).first()
    
    if not conversation:
        # Create one if it doesn't exist
        platform_name = msg_in.platform
        
        # If they are on telegram, they should only be talking to their personal bot, so we need the exact token name.
        # But for general and whatsapp, we can just use the provided string.
        # However, to be safe, if they send 'telegram', we can just use 'telegram_default' or let them use it.
        # It's better to just use what the frontend sends.
        conversation = Conversation(user_id=x_user_id, platform=platform_name)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        msg_in.conversation_id = conversation.id

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        sender="user",
        message=msg_in.message
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    
    # Broadcast user message (optional, since sender already adds it optimistically, but good for other clients)
    
    # Generate bot reply
    try:
        import asyncio
        reply_text = await asyncio.wait_for(
            asyncio.to_thread(ask_llm, msg_in.message),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        reply_text = "Error: LLM response timed out after 15 seconds. The API might be down or your key is restricted."
    except Exception as e:
        reply_text = f"Error: {str(e)}"
        
    # Save bot message
    bot_msg = Message(
        conversation_id=conversation.id,
        sender="bot",
        message=reply_text
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    # Broadcast to all connected clients for this user
    await manager.broadcast_to_user(
        str(x_user_id), 
        {
            "id": bot_msg.id,
            "conversation_id": bot_msg.conversation_id,
            "sender": bot_msg.sender,
            "message": bot_msg.message,
            "created_at": bot_msg.created_at.isoformat()
        }
    )

    return bot_msg

@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, x_user_id: int = Header(...), db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == x_user_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or not owned by user")
        
    db.delete(conversation)
    db.commit()
    
    return {"status": "success", "message": "Conversation deleted successfully"}

