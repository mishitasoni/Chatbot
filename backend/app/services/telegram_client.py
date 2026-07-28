import threading
import telebot
import os
import asyncio
from app.services.chatbot import ask_llm
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.ws import manager
from app.database.database import SessionLocal

# Store active bot instances
active_bots = {}

def start_telegram_bot():
    """Starts bots for all users with a telegram token on boot."""
    db = SessionLocal()
    try:
        from app.models.user import User
        try:
            users_with_tokens = db.query(User).filter(User.telegram_bot_token.isnot(None)).all()
            for user in users_with_tokens:
                if user.telegram_bot_token:
                    restart_user_bot(user.id, user.telegram_bot_token)
        except Exception as db_err:
            print(f"[Telegram Client] Skipping boot init, DB not ready: {db_err}")
    finally:
        db.close()

def restart_user_bot(user_id: int, token: str):
    """Starts or restarts a telegram bot for a specific user."""
    if user_id in active_bots:
        try:
            active_bots[user_id].stop_polling()
        except:
            pass
            
    bot = telebot.TeleBot(token)
    active_bots[user_id] = bot
    
    # We need a reference to the main event loop to safely call broadcast_to_user
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    @bot.message_handler(func=lambda message: True)
    def handle_messages(message):
        question = message.text
        print(f"\n[Telegram User {user_id}] You: {question}")
        
        # 1. Save User Message to DB
        db = SessionLocal()
        try:
            platform = "telegram"
            conversation = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.platform == platform
            ).first()
            
            if not conversation:
                conversation = Conversation(user_id=user_id, platform=platform)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
            user_msg = Message(
                conversation_id=conversation.id,
                sender="user",
                message=question
            )
            db.add(user_msg)
            db.commit()
            db.refresh(user_msg)
            
            user_msg_data = {
                "id": user_msg.id,
                "conversation_id": user_msg.conversation_id,
                "sender": user_msg.sender,
                "message": user_msg.message,
                "created_at": user_msg.created_at.isoformat()
            }
            
            # Broadcast to UI safely from thread
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast_to_user(str(user_id), user_msg_data),
                    loop
                )
            else:
                asyncio.run(manager.broadcast_to_user(str(user_id), user_msg_data))
            
            # 2. Get LLM Answer
            raw_answer = ask_llm(question)
            
            from app.utils.format import clean_markdown
            answer = clean_markdown(raw_answer)
            
            print(f"\n[Telegram User {user_id}] Bot: {answer}")
            
            # 3. Save Bot Message to DB
            bot_msg = Message(
                conversation_id=conversation.id,
                sender="bot",
                message=answer
            )
            db.add(bot_msg)
            db.commit()
            db.refresh(bot_msg)
            
            bot_msg_data = {
                "id": bot_msg.id,
                "conversation_id": bot_msg.conversation_id,
                "sender": bot_msg.sender,
                "message": bot_msg.message,
                "created_at": bot_msg.created_at.isoformat()
            }
            
            # Broadcast to UI safely from thread
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast_to_user(str(user_id), bot_msg_data),
                    loop
                )
            else:
                asyncio.run(manager.broadcast_to_user(str(user_id), bot_msg_data))
            
            # 4. Reply to Telegram
            max_length = 4000
            if len(answer) > max_length:
                for i in range(0, len(answer), max_length):
                    bot.reply_to(message, answer[i:i+max_length])
            else:
                bot.reply_to(message, answer)
                
        except Exception as e:
            print(f"[Telegram User {user_id}] Error: {e}")
            bot.reply_to(message, "Sorry, an error occurred.")
        finally:
            db.close()

    print(f"========================================")
    print(f" Telegram Bot for User {user_id} is running! ")
    print(f" Waiting for messages... ")
    print(f"========================================")
    
    # Run polling in a background thread so it doesn't block the caller
    import threading
    thread = threading.Thread(target=bot.infinity_polling, daemon=True)
    thread.start()
