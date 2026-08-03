import httpx
from typing import Optional

NODE_SERVICE_URL = "http://127.0.0.1:3001"

def get_qr_for_user(user_id: int) -> Optional[str]:
    """
    Calls the Node.js microservice to get the QR code for a specific user.
    """
    try:
        response = httpx.get(f"{NODE_SERVICE_URL}/qr/{user_id}", timeout=25.0)
        data = response.json()
        
        if data.get("status") == "connected":
            return "CONNECTED"
        return data.get("qr")
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
                f"{NODE_SERVICE_URL}/send",
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
