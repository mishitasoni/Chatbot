import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_ws():
    url = os.getenv("OPENCLAW_WS_URL")
    token = os.getenv("OPENCLAW_GATEWAY_TOKEN")
    async with websockets.connect(url) as ws:
        async for msg in ws:
            data = json.loads(msg)
            print("Received:", data.get("type"), data.get("event") or data.get("id"))
            with open("test_output.txt", "a") as f:
                f.write(msg + "\n")
            
            if data.get("event") == "connect.challenge":
                payload = {
                    "type": "req",
                    "id": "init",
                    "method": "connect",
                    "params": {
                        "role": "operator",
                        "scopes": ["operator.read", "operator.write"],
                        "client": {
                            "id": "cli",
                            "mode": "probe",
                            "platform": "win32",
                            "version": "1.0.0"
                        },
                        "auth": {"token": token}
                    }
                }
                await ws.send(json.dumps(payload))
            elif data.get("id") == "init" and data.get("ok"):
                payload = {
                    "type": "req",
                    "id": "sub",
                    "method": "sessions.messages.subscribe",
                    "params": {}
                }
                await ws.send(json.dumps(payload))

asyncio.run(test_ws())
