import asyncio
import websockets
import json
import os
MOCK_USER_ID = 1
from app.services.chatbot import ask_llm
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager
from app.database.database import SessionLocal

async def process_message(data, websocket=None):
    if data.get("type") != "event":
        return None
        
    event_type = data.get("event")
    payload = data.get("payload", {})
    
    print(f"\n[OpenClaw DEBUG] Event: {event_type}")
    
    if event_type == "session.message":
        # Usually payload contains sessionKey and message object
        session_key = payload.get("sessionKey", payload.get("key", ""))
        message = payload.get("message", {})
        
        Body = message.get("text", "") or message.get("content", "") or message.get("body", "")
        if not Body and "parts" in message:
            Body = str(message.get("parts"))
            
        sender_role = message.get("role", "")  # 'user' or 'assistant'
        if not sender_role:
            sender_role = "user" if message.get("type") == "inbound" else "bot"
            
        if not Body:
            print(f"[OpenClaw WS] Empty body in message: {message}")
            return None
            
        platform = "telegram"
        if "whatsapp" in session_key:
            platform = "whatsapp"
        elif "dashboard" in session_key or "webchat" in session_key:
            platform = "dashboard"
            
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

            # 2. Save message
            db_sender = "bot" if sender_role in ["assistant", "bot"] else "user"
            msg = Message(
                conversation_id=conversation.id,
                sender=db_sender,
                message=Body
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            # 3. Broadcast to frontend
            await manager.broadcast_to_user(
                str(MOCK_USER_ID), 
                {
                    "id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "sender": msg.sender,
                    "message": msg.message,
                    "created_at": msg.created_at.isoformat()
                }
            )
            
            print(f"\n[OpenClaw WS] Processed {db_sender} message on {platform}: {Body}")
            
            # 4. If it's a user message, reply via LLM
            if db_sender == "user":
                answer = await asyncio.to_thread(ask_llm, Body)
                bot_msg = Message(
                    conversation_id=conversation.id,
                    sender="bot",
                    message=answer
                )
                db.add(bot_msg)
                db.commit()
                db.refresh(bot_msg)
                
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
                
                print(f"\n[OpenClaw WS] Bot generated reply: {answer}")
                
                if websocket:
                    reply_payload = {
                        "type": "req",
                        "id": f"reply_{bot_msg.id}",
                        "method": "sessions.messages.send",
                        "params": {
                            "sessionKey": session_key,
                            "message": {
                                "type": "text",
                                "text": answer
                            }
                        }
                    }
                    await websocket.send(json.dumps(reply_payload))
            
        except Exception as e:
            print(f"[OpenClaw WS] DB Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
            
    return None

async def openclaw_client():
    ws_url = os.getenv("OPENCLAW_WS_URL")
    token = os.getenv("OPENCLAW_GATEWAY_TOKEN")
    
    if not ws_url or not token:
        print("[OpenClaw WS] Configuration missing, skipping connection.")
        return

    while True:
        try:
            print(f"[OpenClaw WS] Connecting to {ws_url}...")
            async with websockets.connect(ws_url) as websocket:
                print("[OpenClaw WS] Connected! Sending handshake...")
                
                # We don't send auth_payload immediately. We wait for connect.challenge.
                
                async for message in websocket:
                    try:
                        with open("e:/Chatbot/backend/openclaw_debug2.log", "a", encoding="utf-8") as f:
                            f.write(message + "\n")
                            
                        data = json.loads(message)
                        
                        if data.get("type") == "res" and data.get("id") == "init_connect":
                            print(f"[OpenClaw WS] Handshake response: {data}")
                            if data.get("ok"):
                                # Send subscribe
                                sub_payload = {
                                    "type": "req",
                                    "id": "sub_messages",
                                    "method": "sessions.messages.subscribe",
                                    "params": {}
                                }
                                print(f"[OpenClaw WS] Sending subscribe: {sub_payload}")
                                await websocket.send(json.dumps(sub_payload))
                            else:
                                print(f"[OpenClaw WS] Handshake FAILED: {data}")
                            continue
                            
                        if data.get("type") == "event" and data.get("event") == "connect.challenge":
                            print(f"[OpenClaw WS] Received challenge: {data}")
                            auth_payload = {
                                "type": "req",
                                "id": "init_connect",
                                "method": "connect",
                                "params": {
                                    "minProtocol": 4,
                                    "maxProtocol": 4,
                                    "role": "operator",
                                    "scopes": ["operator.read", "operator.write"],
                                    "client": {
                                        "id": "cli",
                                        "mode": "probe",
                                        "platform": "win32",
                                        "version": "1.0.0"
                                    },
                                    "auth": {
                                        "token": token
                                    }
                                }
                            }
                            print(f"[OpenClaw WS] Sending auth: {auth_payload}")
                            await websocket.send(json.dumps(auth_payload))
                            continue
                            
                        if data.get("type") == "res" and data.get("id") == "sub_messages":
                            print(f"[OpenClaw WS] Subscribe response: {data}")
                            continue

                        await process_message(data, websocket)
                        
                    except json.JSONDecodeError:
                        print("[OpenClaw WS] Failed to decode message.")
                    except Exception as e:
                        print(f"[OpenClaw WS] Error processing message: {e}")
        except Exception as e:
            print(f"[OpenClaw WS] Connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
