import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.user import router as user_router
from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router
from app.api.ws import router as ws_router
from app.api.openai_proxy import router as openai_proxy_router
from app.services.telegram_client import start_telegram_bot
import threading

app = FastAPI(
    title="Doubtnut Chatbot",
    version="1.0"
)

from app.services.openclaw_poller import start_openclaw_poller

@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=start_telegram_bot, daemon=True)
    thread.start()
    start_openclaw_poller()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.integrations import router as integrations_router
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(ws_router)
app.include_router(openai_proxy_router)
app.include_router(integrations_router)

@app.get("/")
def home():
    return {"message": "Backend Running"}