import os
import httpx
from fastapi import APIRouter, Request, Depends, BackgroundTasks, HTTPException, Query
from sqlalchemy.orm import Session

from app.services.chatbot import ask_llm
from app.database.dependencies import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager
from app.services.user_service import get_or_create_user_by_phone
from app.services.whatsapp_manager import send_whatsapp_message

router = APIRouter()

ALLOWED_WHATSAPP_NUMBER = os.getenv("ALLOWED_WHATSAPP_NUMBER", "")

async def process_whatsapp_message(body: str, from_number: str, bot_user_id: int = None, from_me: bool = False, is_self_chat: bool = False):
    # Standardize the phone number with a + if it doesn't have one
    phone_number = f"+{from_number.replace('@c.us', '').replace('@lid', '')}" if not from_number.startswith('+') else from_number.replace('@c.us', '').replace('@lid', '')

    if ALLOWED_WHATSAPP_NUMBER and not phone_number.endswith(ALLOWED_WHATSAPP_NUMBER.replace('+', '')):
        print(f"[WhatsApp] Ignoring message from {phone_number} because it is not the ALLOWED_WHATSAPP_NUMBER.")
        return

    from app.database.database import SessionLocal
    db = SessionLocal()
    try:
        if bot_user_id is not None:
            user_id = int(bot_user_id)
        else:
            user = get_or_create_user_by_phone(db, phone_number)
            user_id = user.id

        # 1. Find or create conversation
        conversation = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.platform == f"whatsapp_{phone_number}"
        ).first()
        
        if not conversation:
            conversation = Conversation(user_id=user_id, platform=f"whatsapp_{phone_number}")
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # 2. Save user message (if fromMe is true, it means the user sent it from their phone. We still save it as sender="user" so it shows on the right side of the UI)
        user_msg = Message(
            conversation_id=conversation.id,
            sender="user",
            message=body
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 3. Broadcast incoming message to the UI
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

        # Check if it's a self-chat securely using the database
        is_safe_self_chat = is_self_chat
        
        if from_me and not is_safe_self_chat:
            # Fallback 1: Check against the user's registered phone number in the DB
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.phone:
                db_phone = user.phone.replace('+', '')
                req_phone = phone_number.replace('+', '')
                if req_phone.endswith(db_phone) or db_phone.endswith(req_phone):
                    is_safe_self_chat = True
                    
            # Fallback 2: Check against ALLOWED_WHATSAPP_NUMBER
            if not is_safe_self_chat and ALLOWED_WHATSAPP_NUMBER:
                allowed_phone = ALLOWED_WHATSAPP_NUMBER.replace('+', '')
                req_phone = phone_number.replace('+', '')
                if req_phone.endswith(allowed_phone) or allowed_phone.endswith(req_phone):
                    is_safe_self_chat = True

        # If it's an outbound message to another user, DO NOT generate a bot reply!
        if from_me and not is_safe_self_chat:
            print(f"[WhatsApp] Outbound message to another user detected (or self-chat detection failed). Skipping bot reply.")
            return

        # 4. Ask LLM
        try:
            answer = await asyncio.to_thread(ask_llm, body)
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

        # 6. Broadcast outgoing message to the UI
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

        # 7. Send back via Node.js Microservice
        if bot_user_id:
            success = await send_whatsapp_message(bot_user_id, from_number, answer)
            if not success:
                print("[WhatsApp Node] Error sending message via Node service.")
        else:
            print("[WhatsApp Node] No bot_user_id provided, cannot send reply.")
    except Exception as e:
        import traceback
        print(f"[WhatsApp] Unhandled Exception in process_whatsapp_message: {e}")
        traceback.print_exc()
    finally:
        db.close()

@router.post("/whatsapp/webhook/node")
async def receive_node_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive incoming messages from the Node.js whatsapp-web.js microservice.
    """
    try:
        data = await request.json()
        user_id = data.get("userId")
        from_number = data.get("from")
        body = data.get("body", "")
        media_base64 = data.get("mediaBase64")
        mime_type = data.get("mimeType", "image/jpeg")
        from_me = data.get("fromMe", False)
        is_self_chat = data.get("isSelfChat", False)
        
        if media_base64:
            body = f"![image](data:{mime_type};base64,{media_base64})\n\n{body}"
        
        if user_id and from_number and body:
            background_tasks.add_task(process_whatsapp_message, body, from_number, user_id, from_me, is_self_chat)
            
    except Exception as e:
        print(f"[WhatsApp Node] Error parsing webhook: {e}")
        
    return {"status": "ok"}
