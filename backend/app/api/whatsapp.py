import os
import httpx
from fastapi import APIRouter, Request, Depends, BackgroundTasks, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.services.chatbot import ask_llm
from app.database.dependencies import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager
from app.services.user_service import get_or_create_user_by_phone
from app.services.whatsapp_manager import send_whatsapp_message

router = APIRouter()

# Meta credentials from environment variables
META_WHATSAPP_TOKEN = os.getenv("META_WHATSAPP_TOKEN")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")
# Provide a fallback for the verify token so you can use it immediately for setup
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "doubtnut_webhook_secret")
ALLOWED_WHATSAPP_NUMBER = os.getenv("ALLOWED_WHATSAPP_NUMBER", "")

async def process_meta_whatsapp_message(body: str, from_number: str, bot_user_id: int = None):
    try:
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

            # 2. Save user message
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
            await manager.broadcast_to_all(
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
            await manager.broadcast_to_all(
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
                # Fallback to Meta Graph API if it was a Meta webhook
                if META_WHATSAPP_TOKEN and META_PHONE_NUMBER_ID:
                    url = f"https://graph.facebook.com/v19.0/{META_PHONE_NUMBER_ID}/messages"
                    headers = {
                        "Authorization": f"Bearer {META_WHATSAPP_TOKEN}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": from_number,
                        "type": "text",
                        "text": {"preview_url": False, "body": answer}
                    }
                    async with httpx.AsyncClient() as client:
                        try:
                            response = await client.post(url, headers=headers, json=payload)
                            response.raise_for_status()
                        except Exception as e:
                            print(f"[WhatsApp Meta] Error sending message: {e}")
                else:
                    print("[WhatsApp Node] No bot_user_id provided, cannot send reply.")
    except Exception as e:
        import traceback
        print(f"[WhatsApp] Unhandled Exception in process_meta_whatsapp_message: {e}")
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
        
        if media_base64:
            body = f"![image](data:{mime_type};base64,{media_base64})\n\n{body}"
        
        if user_id and from_number and body:
            # We already know the user_id this bot belongs to!
            # But the 'from' is the phone number of the person texting the bot.
            # We can process it the same way.
            background_tasks.add_task(process_meta_whatsapp_message, body, from_number, user_id)
            
    except Exception as e:
        print(f"[WhatsApp Node] Error parsing webhook: {e}")
        
    return {"status": "ok"}


@router.get("/whatsapp/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Meta requires a GET request to verify the webhook URL during setup.
    """
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        print("[WhatsApp Meta] Webhook verified successfully!")
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/whatsapp/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive incoming messages from Meta WhatsApp API.
    """
    try:
        data = await request.json()
        
        # Meta's payload structure
        if "entry" in data and len(data["entry"]) > 0:
            for entry in data["entry"]:
                if "changes" in entry and len(entry["changes"]) > 0:
                    change = entry["changes"][0]
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        
                        # Check if this is an actual message (and not a status update like "read" or "delivered")
                        if "messages" in value and len(value["messages"]) > 0:
                            message_data = value["messages"][0]
                            
                            from_number = message_data.get("from")
                            
                            # Handle text messages
                            if message_data.get("type") == "text":
                                body = message_data.get("text", {}).get("body", "")
                                
                                if from_number and body:
                                    background_tasks.add_task(process_meta_whatsapp_message, body, from_number)
                                    
    except Exception as e:
        print(f"[WhatsApp Meta] Error parsing webhook: {e}")
        
    # Always return 200 OK so Meta knows we received the webhook successfully
    return {"status": "ok"}
