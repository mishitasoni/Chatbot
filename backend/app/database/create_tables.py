from app.database.database import Base, engine, SessionLocal
from app.models import User, Conversation, Message

Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")

# Insert mock user for testing
db = SessionLocal()
try:
    mock_user = db.query(User).filter(User.id == 1).first()
    if not mock_user:
        mock_user = User(id=1, name="Test User", email="test@example.com")
        db.add(mock_user)
        db.commit()
        print("✅ Mock user created successfully!")
except Exception as e:
    print(f"Error creating mock user: {e}")
finally:
    db.close()