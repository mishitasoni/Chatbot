from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services.chatbot import ask_llm
from app.database.dependencies import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager

router = APIRouter()

MOCK_USER_ID = 1

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        print(f"\n[Raw Payload Received]: {data}")
        Body = data.get("message", data.get("Body", ""))
        From = data.get("from", data.get("From", data.get("sender", "")))
    except Exception:
        form_data = await request.form()
        print(f"\n[Raw Form Data]: {form_data}")
        Body = form_data.get("Body", "")
        From = form_data.get("From", "")

    print(f"\n[WhatsApp] You ({From}): {Body}")

    # 1. Find or create conversation for this platform
    conversation = db.query(Conversation).filter(
        Conversation.user_id == MOCK_USER_ID,
        Conversation.platform == "whatsapp"
    ).first()
    
    if not conversation:
        conversation = Conversation(user_id=MOCK_USER_ID, platform="whatsapp")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        sender="user",
        message=Body
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 3. Broadcast incoming message to frontend
    await manager.broadcast_to_user(
        str(MOCK_USER_ID), 
        {
            "id": user_msg.id,
            "conversation_id": user_msg.conversation_id,
            "sender": user_msg.sender,
            "message": user_msg.message,
            "created_at": user_msg.created_at.isoformat()
        }
    )

    # 4. Generate answer
    try:
        answer = ask_llm(Body)
    except Exception as e:
        answer = f"Sorry, an error occurred: {str(e)}"
    
    print(f"\n[WhatsApp] Bot: {answer}\n")

    # 5. Save bot message
    bot_msg = Message(
        conversation_id=conversation.id,
        sender="bot",
        message=answer
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    # 6. Broadcast outgoing message to frontend
    await manager.broadcast_to_user(
        str(MOCK_USER_ID), 
        {
            "id": bot_msg.id,
            "conversation_id": bot_msg.conversation_id,
            "sender": bot_msg.sender,
            "message": bot_msg.message,
            "created_at": bot_msg.created_at.isoformat()
        }
    )

    # 7. Generate JSON response for OpenClaw
    return {"status": "success", "message": answer}
