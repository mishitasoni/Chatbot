from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.dependencies import get_db
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

class TelegramTokenRequest(BaseModel):
    user_id: int
    token: str

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

@router.get("/test_token")
def test_token():
    import subprocess
    try:
        process = subprocess.Popen(["python", "e:\\Chatbot\\query_db.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        out, err = process.communicate(timeout=5)
        with open("e:\\Chatbot\\db_out.txt", "r") as f:
            return {"output": f.read()}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug_openclaw")
def debug_openclaw():
    import subprocess
    import threading
    import time
    
    def run_cmd():
        try:
            # We must use shell=True on Windows if openclaw is a .cmd file
            process = subprocess.Popen(
                "openclaw channels login --channel whatsapp > e:\\Chatbot\\test_qr_out.txt 2>&1",
                shell=True
            )
            time.sleep(10) # wait 10 seconds to collect output
            process.kill()
        except Exception as e:
            with open("e:\\Chatbot\\test_qr_out.txt", "w") as f:
                f.write(str(e))
            
    t = threading.Thread(target=run_cmd)
    t.start()
    t.join(timeout=15)
    
    try:
        with open("e:\\Chatbot\\test_qr_out.txt", "r") as f:
            return {"output": f.read()}
    except Exception as e:
        return {"status": "error", "error": str(e)}



@router.get("/debug_db")
def debug_openclaw_db():
    import sqlite3
    import os
    home = os.path.expanduser("~")
    db_path = os.path.join(home, ".openclaw", "state", "openclaw.sqlite")
    if not os.path.exists(db_path):
        return {"error": "no db"}
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    
    res = {"tables": [t[0] for t in tables]}
    
    # Try to grab 5 rows from channel_pairing_requests if it exists
    if "channel_pairing_requests" in res["tables"]:
        rows = con.execute("SELECT * FROM channel_pairing_requests ORDER BY rowid DESC LIMIT 5").fetchall()
        res["channel_pairing_requests"] = rows
        
    return res
