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
    
    # The WhatsApp Node.js microservice is managed by start.sh on deployment.
    # It should be run manually locally or via a script, not inside FastAPI.

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
            
    # Node process is managed externally

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

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
assets_dir = os.path.join(frontend_dist, "assets")
index_file = os.path.join(frontend_dist, "index.html")

if os.path.exists(frontend_dist) and os.path.exists(index_file):
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(index_file)
else:
    @app.get("/")
    def home():
        return {"message": "Backend Running, but frontend dist or index.html not found"}