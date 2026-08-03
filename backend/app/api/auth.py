from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re

from app.database.dependencies import get_db
from app.schemas.user import UserLogin, UserResponse, UserCreate
from app.services import user_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login", response_model=UserResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    # Try to find user by email or phone
    user = None
    if login_data.email:
        user = user_service.get_user_by_email(db, login_data.email)
    elif login_data.phone:
        # Normalize phone just in case
        phone = login_data.phone.strip()
        # Ensure it has + prefix if it's purely digits and country code (naive fallback)
        if re.match(r'^\d+$', phone) and len(phone) >= 10:
            phone = f"+{phone}"
            
        from app.models.user import User
        user = db.query(User).filter(
            (User.phone == login_data.phone) | 
            (User.phone == phone)
        ).first()

    # If user not found, create one automatically
    if not user:
        new_user = UserCreate(
            name="New User",
            email=login_data.email,
            phone=login_data.phone
        )
        user = user_service.create_user(db, new_user)

    return user