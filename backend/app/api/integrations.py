from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.dependencies import get_db
from app.models.user import User
from pydantic import BaseModel
from app.models.user_channel import UserChannel
router = APIRouter(prefix="/api/integrations", tags=["integrations"])

class TelegramTokenRequest(BaseModel):
    user_id: int
    token: str

class ChannelActionRequest(BaseModel):
    user_id: int

@router.post("/telegram")
def link_telegram(request: TelegramTokenRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Validate the token synchronously before saving it
    import telebot
    try:
        bot = telebot.TeleBot(request.token)
        bot.get_me() # This will throw an exception if the token is invalid (e.g. 401 Unauthorized)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid Telegram token. Please ensure you copied the full token.")
        
    user.telegram_bot_token = request.token
    db.commit()
    
    # Pre-create a new conversation for this bot token if it doesn't exist
    from app.models.conversation import Conversation
    try:
        bot_info = bot.get_me()
        bot_name = bot_info.first_name
    except:
        bot_name = request.token[:10] if request.token else "default"
    platform_key = f"telegram_{bot_name}"
    
    existing_conv = db.query(Conversation).filter(
        Conversation.user_id == user.id,
        Conversation.platform == platform_key
    ).first()
    
    if not existing_conv:
        new_conv = Conversation(user_id=user.id, platform=platform_key)
        db.add(new_conv)
        db.commit()

    # Restart telegram manager for this user
    from app.services.telegram_client import restart_user_bot
    restart_user_bot(user.id, request.token)
    
    return {"message": "Telegram linked successfully"}




@router.get("/whatsapp/qr/{user_id}")
def get_whatsapp_qr(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Ask whatsapp_manager to generate QR code string (will be implemented next)
    from app.services.whatsapp_manager import get_qr_for_user
    qr_code = get_qr_for_user(user.id)
    
    if qr_code:
        return {"qr": qr_code}
    return {"message": "QR code not ready yet, try again"}, 202

@router.get("/channels/status/{user_id}")
def get_channel_status(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    channels = db.query(UserChannel).filter(UserChannel.user_id == user_id).all()
    
    has_whatsapp = any(c.channel_type == 'whatsapp' for c in channels)
    has_telegram = any(c.channel_type == 'telegram' for c in channels)
    
    res = [
        {
            "channel_type": c.channel_type,
            "status": c.status,
            "phone_number": c.phone_number
        }
        for c in channels
    ]
    
    if not has_whatsapp:
        res.append({
            "channel_type": "whatsapp",
            "status": "disconnected",
            "phone_number": None
        })
        
    if not has_telegram:
        # Check if they have a bot token in the user record
        if user and user.telegram_bot_token:
            res.append({
                "channel_type": "telegram",
                "status": "connected",
                "phone_number": None
            })
        else:
            res.append({
                "channel_type": "telegram",
                "status": "disconnected",
                "phone_number": None
            })
            
    return res

@router.post("/channels/whatsapp/disconnect")
def disconnect_whatsapp(request: ChannelActionRequest, db: Session = Depends(get_db)):
    channel = db.query(UserChannel).filter(
        UserChannel.user_id == request.user_id,
        UserChannel.channel_type == "whatsapp"
    ).first()
    
    if channel:
        channel.status = "disconnected"
        channel.phone_number = None
        db.commit()
        
    import subprocess
    try:
        subprocess.run(["openclaw.cmd", "channels", "remove", "--channel", "whatsapp", "--account", f"user_{request.user_id}"])
    except:
        pass
        
    return {"status": "success", "message": "Disconnected"}

@router.post("/channels/telegram/disconnect")
def disconnect_telegram(request: ChannelActionRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if user:
        user.telegram_bot_token = None
        db.commit()
        
    return {"status": "success", "message": "Telegram disconnected"}
