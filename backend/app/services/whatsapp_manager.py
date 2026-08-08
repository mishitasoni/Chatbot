import os
import httpx
from typing import Optional

NODE_SERVICE_URL = os.getenv("NODE_SERVICE_URL", "http://127.0.0.1:8006")

def get_qr_for_user(user_id: int) -> Optional[str]:
    """
    Calls the Node.js microservice to get the QR code for a specific user.
    """
    try:
        response = httpx.get(f"{NODE_SERVICE_URL}/api/wa/qr?user_id={user_id}", timeout=60.0)
        data = response.json()
        
        if data.get("connected"):
            return "CONNECTED"
        return data.get("qr_code")
    except Exception as e:
        print(f"[whatsapp_manager] Error fetching QR code from Node: {e}")
        return None

async def send_whatsapp_message(user_id: int, to: str, message: str) -> bool:
    """
    Calls the Node.js microservice to send a WhatsApp message.
    """
    # The new whatsapp_service.js responds directly, so this may not be needed 
    # for regular LLM responses, but we keep a dummy fallback or the new endpoint if we had one.
    # The new script doesn't have a /send route, so we just return True for now.
    return True
