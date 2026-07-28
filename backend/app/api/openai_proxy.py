import uuid
import time
import asyncio
import re
from fastapi import APIRouter, Request
from app.database.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager
from app.services.chatbot import ask_llm

router = APIRouter()

MOCK_USER_ID = 1

def clean_user_message(raw_text: str) -> str:
    if not raw_text:
        return ""
    cleaned = raw_text
    # Remove code blocks like ```json ... ``` or ``` ... ```
    cleaned = re.sub(r'```[\s\S]*?```', '', cleaned)
    # Remove metadata lines starting with [Date...] down to colons
    cleaned = re.sub(r'\[.*?\]\s*Conversation info.*?:?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Sender\s*\(.*?\):?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\(untrusted metadata\):?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'```\s*', '', cleaned)
    cleaned = cleaned.strip()
    return cleaned if cleaned else raw_text.strip()

@router.post("/v1/chat/completions")
@router.post("/v1/responses")
async def chat_completions(req: Request):
    raw_body = await req.body()
    try:
        data = await req.json()
    except:
        data = {}
        
    messages = data.get("messages", [])
    model = data.get("model", "gpt-3.5-turbo")
    
    question = ""
    session_id = data.get("user", "")
    
    if messages:
        last_user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), None)
        if last_user_msg:
            question = last_user_msg.get("content", "")
    else:
        # Fallback if AI just sends arbitrary JSON or raw text
        if data:
            question = data.get("prompt", data.get("message", data.get("content", str(data))))
            session_id = data.get("session_id", session_id)
        else:
            question = raw_body.decode("utf-8")
            
    if not question:
        return {"error": "no prompt found"}
        
    actual_prompt = clean_user_message(question)
    
    raw_prompt_search = (question + " " + str(session_id) + " " + str(messages)).lower()
    phone_match = re.search(r'\+?(\d{10,12})', question)

    if "whatsapp" in raw_prompt_search:
        if phone_match:
            session_id = f"whatsapp_{phone_match.group(1)}"
        elif "whatsapp_" in str(data):
            match = re.search(r'(whatsapp_\+?\d+)', str(data))
            if match:
                session_id = match.group(1)
        elif not session_id or session_id == "default":
            session_id = "whatsapp_default"
            
    if not session_id or "whatsapp_" not in session_id:
        session_id = "whatsapp_unknown"
        
    platform = "whatsapp"
    
    db = SessionLocal()
    try:
        # 1. Find or create conversation for this platform
        conversation = db.query(Conversation).filter(
            Conversation.user_id == MOCK_USER_ID,
            Conversation.platform == platform
        ).first()
        
        if not conversation:
            conversation = Conversation(user_id=MOCK_USER_ID, platform=platform)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
        # 2. Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            sender="user",
            message=actual_prompt
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)
        
        # 3. Broadcast user message
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
        
        # 4. Generate AI reply
        answer = await asyncio.to_thread(ask_llm, actual_prompt)
        
        # 5. Save bot reply
        bot_msg = Message(
            conversation_id=conversation.id,
            sender="bot",
            message=answer
        )
        db.add(bot_msg)
        db.commit()
        db.refresh(bot_msg)
        
        # 6. Broadcast bot reply
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
        
    except Exception as e:
        print(f"[OpenAI Proxy] DB Error: {e}")
        answer = "Sorry, there was an internal server error."
    finally:
        db.close()
        
    # 7. Return OpenAI format
    response_id = f"chatcmpl-{uuid.uuid4().hex}"
    
    is_responses_endpoint = req.url.path.endswith("/responses")
    
    return {
        "id": response_id,
        "object": "response" if is_responses_endpoint else "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer
                },
                "finish_reason": "stop"
            }
        ],
        "output": [
            {
                "id": f"msg-{uuid.uuid4().hex[:12]}",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": answer
                    }
                ]
            }
        ],
        "output_text": answer,
        "usage": {
            "prompt_tokens": len(actual_prompt) // 4,
            "completion_tokens": len(answer) // 4,
            "total_tokens": (len(actual_prompt) + len(answer)) // 4
        }
    }
