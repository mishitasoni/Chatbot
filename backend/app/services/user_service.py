from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_all_users(db: Session):
    return db.query(User).all()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_or_create_user_by_phone(db: Session, phone: str):
    norm_phone = f"+{phone}" if not phone.startswith("+") else phone
    user = db.query(User).filter(
        (User.phone == phone) | (User.phone == norm_phone)
    ).first()
        
    if not user:
        # Fallback to the first user in the system (the one logged into the UI)
        # to ensure WhatsApp messages show up in their dashboard
        first_user = db.query(User).first()
        if first_user:
            first_user.phone = norm_phone
            db.commit()
            return first_user
            
        new_user = UserCreate(name="WhatsApp User", phone=norm_phone)
        user = create_user(db, new_user)
        
    return user