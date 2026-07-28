import os
import time
import sqlite3
import subprocess
import asyncio
from datetime import datetime

from app.database.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager
from app.services.chatbot import ask_llm

MOCK_USER_ID = 1
DB_PATH = r"C:\Users\mishs\.openclaw\state\openclaw.sqlite"
LAST_ID_FILE = "whatsapp_last_id.txt"

def get_last_id():
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return 0

def set_last_id(last_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(last_id))

async def handle_new_message(msg_id, sender, text):
    print(f"\n[WhatsApp Poller] New msg from {sender}: {text}")
    db = SessionLocal()
    try:
        # 1. Find or create conversation
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
            message=text
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 3. Broadcast incoming message
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

        # 4. Generate answer via LLM
        answer = await asyncio.to_thread(ask_llm, text)
        print(f"\n[WhatsApp Poller] Bot reply: {answer}\n")

        # 5. Send reply via OpenClaw CLI
        # openclaw message send --channel whatsapp --target <Number> --message <Reply>
        subprocess.run([
            "openclaw.cmd", "message", "send", 
            "--channel", "whatsapp", 
            "--target", sender, 
            "--message", answer
        ], shell=True)

        # 6. Save bot message
        bot_msg = Message(
            conversation_id=conversation.id,
            sender="bot",
            message=answer
        )
        db.add(bot_msg)
        db.commit()
        db.refresh(bot_msg)

        # 7. Broadcast outgoing message
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
        print(f"[WhatsApp Poller] Error handling message: {e}")
    finally:
        db.close()

def parse_openclaw_messages():
    # Attempt to read OpenClaw DB
    try:
        # Use URI for read-only mode to prevent lock conflicts
        uri = f"file:{DB_PATH.replace(chr(92), '/')}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=10.0)
        
        # Check schema first time
        if not hasattr(parse_openclaw_messages, 'schema_printed'):
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            print(f"[WhatsApp Poller] Found tables: {tables}")
            parse_openclaw_messages.schema_printed = True
            
            # Print messages schema if exists
            if any(t[0] == 'messages' for t in tables):
                schema = conn.execute("PRAGMA table_info(messages)").fetchall()
                print(f"[WhatsApp Poller] messages schema: {schema}")
            elif any(t[0] == 'message' for t in tables):
                schema = conn.execute("PRAGMA table_info(message)").fetchall()
                print(f"[WhatsApp Poller] message schema: {schema}")

        output = ""
        for table in ['delivery_queue_entries', 'task_runs', 'plugin_state_entries', 'channel_ingress_events']:
            try:
                schema = conn.execute(f"PRAGMA table_info({table})").fetchall()
                rows = conn.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 3").fetchall()
                output += f"\n--- {table} ---\nSchema: {schema}\nRows: {rows}\n"
            except:
                pass
                
        with open('channel_info.txt', 'w') as f:
            f.write(output)
        
        table_name = 'channel_ingress_events'
        if not table_name:
            print(f"[WhatsApp Poller] Could not find messages table. Found: {tables}")
            with open('found_tables.txt', 'w') as f:
                f.write(str(tables))
            conn.close()
            return

        # We will attempt a generic query, we might need to adjust columns based on schema
        query = f"SELECT id, text, sender, role FROM {table_name} WHERE id > ? ORDER BY id ASC"
        
        try:
            rows = conn.execute(query, (last_id,)).fetchall()
        except sqlite3.OperationalError as e:
            # Maybe column names differ
            if "no such column" in str(e):
                # Try generic columns
                query2 = f"SELECT * FROM {table_name} WHERE rowid > ? ORDER BY rowid ASC"
                rows = conn.execute(query2, (last_id,)).fetchall()
                # Print row structure to debug
                if rows:
                    print(f"[WhatsApp Poller] Raw rows: {rows}")
                    # Process manually if we can guess
                    # For now, let's just log it and update last_id
                    for r in rows:
                        last_id = r[0] # assume first is ID or rowid
                    set_last_id(last_id)
                conn.close()
                return
            else:
                raise e

        # If we got rows with id, text, sender, role
        for row in rows:
            msg_id, text, sender, role = row
            if role != "bot" and role != "assistant" and text:
                # Need an event loop to run async handle_new_message
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                loop.run_until_complete(handle_new_message(msg_id, sender, text))
            
            last_id = msg_id
            
        set_last_id(last_id)
        
    except Exception as e:
        print(f"[WhatsApp Poller] Database Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def start_whatsapp_poller():
    print("========================================")
    print(" WhatsApp SQLite Poller is running! ")
    print("========================================")
    
    while True:
        parse_openclaw_messages()
        time.sleep(2)
