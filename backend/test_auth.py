import asyncio
import websockets
import json

async def test_id(id_val, mode_val):
    try:
        async with websockets.connect("ws://127.0.0.1:18789/") as ws:
            payload = {
                "type": "req",
                "id": "test",
                "method": "connect",
                "params": {
                    "minProtocol": 1,
                    "maxProtocol": 1,
                    "client": {
                        "id": id_val,
                        "mode": mode_val,
                        "platform": "windows",
                        "version": "1.0.0"
                    },
                    "auth": {
                        "token": "140ea20c62a26b8a4f8ba257f1747f213e27b139ae654920"
                    }
                }
            }
            await ws.send(json.dumps(payload))
            res = await ws.recv()
            print(f"ID: {id_val}, Mode: {mode_val} -> {res}")
            if '"ok":true' in res:
                return True
    except Exception as e:
        pass
    return False

async def main():
    ids = ["operator", "node", "client", "web", "mobile", "desktop", "api", "backend", "test", "app", "bot", "agent", "system", "admin", "openclaw.api", "openclaw.web", "ui", "plugin", "gateway"]
    modes = ["agent", "client", "node", "operator", "bot", "backend", "plugin", "observer"]
    try:
        with open("auth_result.txt", "w") as f:
            for i in ids:
                for m in modes:
                    success = await test_id(i, m)
                    if success:
                        f.write(f"SUCCESS: {i}, {m}\n")
                        return
            f.write("No success found.\n")
    except Exception as e:
        with open("auth_error.txt", "w") as f:
            f.write(str(e))
                
asyncio.run(main())
