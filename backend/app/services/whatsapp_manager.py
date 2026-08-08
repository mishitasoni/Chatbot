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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NODE_SERVICE_URL}/api/wa/send",
                json={
                    "userId": str(user_id),
                    "to": to,
                    "message": message
                },
                timeout=15.0
            )
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"[whatsapp_manager] Error sending message via Node: {e}")
        return False
