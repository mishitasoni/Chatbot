import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.conversation import Conversation
from app.models.message import Message
import json

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
db = Session()

convs = db.query(Conversation).all()
print("=== CONVERSATIONS ===")
for c in convs:
    print(f"ID: {c.id}, Platform: {c.platform}, User: {c.user_id}")

msgs = db.query(Message).all()
print("=== MESSAGES ===")
for m in msgs:
    print(f"ID: {m.id}, Conv: {m.conversation_id}, Sender: {m.sender}, Msg: {m.message[:50]}")
