import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def try_ids():
    ws_url = os.getenv("OPENCLAW_WS_URL") or "ws://127.0.0.1:18789/"
    token = os.getenv("OPENCLAW_GATEWAY_TOKEN") or "140ea20c62a26b8a4f8ba257f1747f213e27b139ae654920"
    
    ids_to_try = ["backend", "operator", "agent", "web", "cli", "app", "gateway", "client", "node"]
    
    for client_id in ids_to_try:
        try:
            print(f"Trying id: {client_id}")
            async with websockets.connect(ws_url) as ws:
                challenge = await ws.recv()
                
                auth_payload = {
                    "type": "req",
                    "id": "init_connect",
                    "method": "connect",
                    "params": {
                        "minProtocol": 4,
                        "maxProtocol": 4,
                        "role": "operator",
                        "scopes": ["operator.read", "operator.write"],
                        "client": {
                            "id": client_id,
                            "platform": "win32"
                        },
                        "auth": {
                            "token": token
                        }
                    }
                }
                await ws.send(json.dumps(auth_payload))
                res = json.loads(await ws.recv())
                if res.get("ok"):
                    print(f"SUCCESS with id: {client_id}")
                    return
                else:
                    print(f"Failed {client_id}: {res}")
        except Exception as e:
            print(f"Error {client_id}: {e}")

asyncio.run(try_ids())
