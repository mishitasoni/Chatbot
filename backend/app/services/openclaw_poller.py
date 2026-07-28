import os
import time
import json
import sqlite3
import asyncio
import subprocess
import threading
from app.database.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager
from app.services.chatbot import ask_llm

MOCK_USER_ID = 1

def start_openclaw_poller():
    thread = threading.Thread(target=poll_openclaw_db, daemon=True)
    thread.start()
    print("[System]: OpenClaw database poller started in background.")

def run_async(coro):
    """Utility to run async code from a synchronous thread."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, loop)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)

def save_and_broadcast_message(platform, sender, text):
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(
            Conversation.user_id == MOCK_USER_ID,
            Conversation.platform == platform
        ).first()
        
        if not conversation:
            conversation = Conversation(user_id=MOCK_USER_ID, platform=platform)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
        msg = Message(
            conversation_id=conversation.id,
            sender=sender,
            message=text
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        
        # Broadcast via WebSockets
        run_async(manager.broadcast_to_user(
            str(MOCK_USER_ID), 
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "sender": msg.sender,
                "message": msg.message,
                "created_at": msg.created_at.isoformat()
            }
        ))
        return msg
    except Exception as e:
        print(f"[OpenClaw Poller] DB Error saving message: {e}")
    finally:
        db.close()

def poll_openclaw_db():
    home_dir = os.path.expanduser("~")
    db_path = os.path.join(home_dir, ".openclaw", "state", "openclaw.sqlite")
    
    last_ingress_id = None
    last_delivery_id = None
    
    while not os.path.exists(db_path):
        time.sleep(2)
        
    while True:
        try:
            con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            cursor = con.cursor()
            
            # --- 1. Poll Ingress (User Messages) ---
            if last_ingress_id is None:
                try:
                    cursor.execute("SELECT MAX(rowid) as max_id FROM channel_ingress_events")
                    row = cursor.fetchone()
                    last_ingress_id = row['max_id'] if row and row['max_id'] else 0
                except Exception:
                    last_ingress_id = 0
                    
            cursor.execute("SELECT rowid, * FROM channel_ingress_events WHERE rowid > ? ORDER BY rowid ASC", (last_ingress_id,))
            rows = cursor.fetchall()
            
            for row in rows:
                row_dict = dict(row)
                last_ingress_id = row_dict.get('rowid', last_ingress_id + 1)
                
                text = ""
                channel = row_dict.get('channel_id', row_dict.get('channel', 'OpenClaw'))
                
                if 'payload_json' in row_dict and row_dict['payload_json'] and row_dict['payload_json'] != 'null':
                    try:
                        payload = json.loads(row_dict['payload_json'])
                        text = payload.get('text', payload.get('body', ''))
                        if not text and 'message' in payload and isinstance(payload['message'], dict):
                            msg = payload['message']
                            if 'message' in msg and isinstance(msg['message'], dict):
                                inner = msg['message']
                                text = inner.get('conversation', inner.get('extendedTextMessage', {}).get('text', ''))
                            if not text:
                                text = msg.get('conversation', msg.get('extendedTextMessage', {}).get('text', ''))
                    except: pass
                elif 'text' in row_dict:
                    text = row_dict['text']
                    
                if text and 'whatsapp' in channel.lower():
                    save_and_broadcast_message("whatsapp", "user", text)
                    print(f"[OpenClaw Poller] User -> AI: {text}")

            # --- 2. Poll Delivery Queue (Maya's Replies) ---
            if last_delivery_id is None:
                try:
                    cursor.execute("SELECT MAX(rowid) as max_id FROM delivery_queue_entries")
                    row = cursor.fetchone()
                    last_delivery_id = row['max_id'] if row and row['max_id'] else 0
                except Exception:
                    last_delivery_id = 0
                    
            cursor.execute("SELECT rowid, * FROM delivery_queue_entries WHERE rowid > ? ORDER BY rowid ASC", (last_delivery_id,))
            d_rows = cursor.fetchall()
            
            for row in d_rows:
                row_dict = dict(row)
                last_delivery_id = row_dict.get('rowid', last_delivery_id + 1)
                
                channel = row_dict.get('channel', '')
                entry_json = row_dict.get('entry_json', '{}')
                
                if 'whatsapp' in channel.lower():
                    try:
                        entry = json.loads(entry_json)
                        print(f"[DEBUG] Delivery Entry JSON: {entry_json[:200]}...")
                        payloads = entry.get('payloads', [])
                        text = ""
                        for p in payloads:
                            if 'text' in p:
                                text += p['text'] + "\n"
                        text = text.strip()
                        
                        # Fallback for other formats
                        if not text and 'text' in entry:
                            text = entry['text']
                        if not text and 'message' in entry:
                            text = entry['message'].get('text', '') if isinstance(entry['message'], dict) else str(entry['message'])
                        if not text and 'content' in entry:
                            text = entry['content']
                        if not text and 'body' in entry:
                            text = entry['body']
                            
                        # Extremely aggressive fallback: just find anything that looks like text
                        if not text:
                            # if it's a deeply nested dictionary, just grab the first string that looks like a message
                            entry_str = str(entry)
                            import re
                            # Try to extract the biggest string value from JSON keys that might be text
                            match = re.search(r'["\'](?:text|content|body|message)["\']\s*:\s*["\'](.*?)["\']', entry_json)
                            if match:
                                text = match.group(1)
                            
                        if text:
                            from app.utils.format import clean_markdown
                            clean_text = clean_markdown(text)
                            save_and_broadcast_message("whatsapp", "bot", clean_text)
                            print(f"[OpenClaw Poller] Maya -> User: {clean_text}")
                    except Exception as e:
                        print(f"Error parsing delivery queue: {e}")
                        
            con.close()
        except Exception as e:
            pass
            
        time.sleep(2)
