import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.user import router as user_router
from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router
from app.api.ws import router as ws_router
from app.api.openai_proxy import router as openai_proxy_router

app = FastAPI(
    title="Doubtnut Chatbot",
    version="1.0"
)

from app.services.telegram_client import start_telegram_bot
import threading

import subprocess
import os

node_process = None

@app.on_event("startup")
async def startup_event():
    global node_process
    print("Application started")
    thread = threading.Thread(target=start_telegram_bot, daemon=True)
    thread.start()
    
    # Auto-start the WhatsApp Node.js microservice
    whatsapp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../whatsapp-service"))
    if os.path.exists(whatsapp_dir):
        try:
            import platform
            node_cmd = "node.exe" if platform.system() == "Windows" else "node"
            node_process = subprocess.Popen([node_cmd, "index.js"], cwd=whatsapp_dir, shell=False)
            print(f"[Node Microservice] Started WhatsApp service with PID {node_process.pid}")
        except Exception as e:
            print(f"[Node Microservice] Error starting WhatsApp service: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global node_process
    print("Application shutdown")
    from app.services.telegram_client import active_bots
    for user_id, bot in active_bots.items():
        try:
            bot.stop_polling()
            print(f"[Telegram Client] Stopped polling for User {user_id}")
        except Exception as e:
            print(f"[Telegram Client] Error stopping bot for User {user_id}: {e}")
            
    if node_process:
        print(f"[Node Microservice] Stopping PID {node_process.pid}")
        try:
            node_process.terminate()
        except:
            pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:5174",
        "https://chatfusionbot-five.vercel.app"
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.telegram import router as telegram_router
from app.api.whatsapp import router as whatsapp_router
from app.api.integrations import router as integrations_router

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(ws_router)
app.include_router(openai_proxy_router)
app.include_router(telegram_router)
app.include_router(whatsapp_router)
app.include_router(integrations_router)

@app.get("/")
def home():
    return {"message": "Backend Running"}