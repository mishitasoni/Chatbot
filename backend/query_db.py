from app.database.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message

db = SessionLocal()
convs = db.query(Conversation).all()
for c in convs:
    print(f"Conversation: id={c.id}, user={c.user_id}, platform={c.platform}")
    msgs = db.query(Message).filter(Message.conversation_id == c.id).all()
    print(f"  Messages count: {len(msgs)}")
db.close()
