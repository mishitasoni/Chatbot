import os
import httpx
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.services.chatbot import ask_llm
from app.database.dependencies import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import create_user

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_or_create_user_by_telegram(db: Session, chat_id: str, name: str):
    # We use telegram_bot_token column to store the telegram chat id since we aren't using personal bot tokens anymore.
    user = db.query(User).filter(User.telegram_bot_token == chat_id).first()
    if not user:
        new_user = UserCreate(name=name, phone=None) # They might not have a phone
        user = create_user(db, new_user)
        user.telegram_bot_token = chat_id
        db.commit()
        db.refresh(user)
    return user

async def process_telegram_message(chat_id: str, text: str, name: str, db: Session):
    user = get_or_create_user_by_telegram(db, chat_id, name)
    user_id = user.id

    # 1. Find or create conversation
    conversation = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.platform == "telegram"
    ).first()
    
    if not conversation:
        conversation = Conversation(user_id=user_id, platform="telegram")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        sender="user",
        message=text
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 3. Broadcast incoming
    import asyncio
    await manager.broadcast_to_user(
        str(user_id), 
        {
            "id": user_msg.id,
            "conversation_id": user_msg.conversation_id,
            "sender": user_msg.sender,
            "message": user_msg.message,
            "created_at": user_msg.created_at.isoformat()
        }
    )

    # 4. Ask LLM
    try:
        answer = await asyncio.to_thread(ask_llm, text)
    except Exception as e:
        answer = f"Sorry, an error occurred: {str(e)}"
    
    # 5. Save bot message
    bot_msg = Message(
        conversation_id=conversation.id,
        sender="bot",
        message=answer
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    # 6. Broadcast outgoing
    await manager.broadcast_to_user(
        str(user_id), 
        {
            "id": bot_msg.id,
            "conversation_id": bot_msg.conversation_id,
            "sender": bot_msg.sender,
            "message": bot_msg.message,
            "created_at": bot_msg.created_at.isoformat()
        }
    )

    # 7. Send back via Telegram API
    if TELEGRAM_BOT_TOKEN:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": answer
        }
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                print(f"[Telegram] Error sending message: {e}")
    else:
        print("[Telegram] TELEGRAM_BOT_TOKEN missing, couldn't send reply.")

@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        message = data.get("message", {})
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        text = message.get("text", "")
        name = chat.get("first_name", "Telegram User")

        if not chat_id or not text:
            return {"status": "ignored"}
            
        background_tasks.add_task(process_telegram_message, chat_id, text, name, db)
    except Exception as e:
        print(f"[Telegram] Webhook parsing error: {e}")

    return {"status": "ok"}
