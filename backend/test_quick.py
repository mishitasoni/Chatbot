import asyncio
import websockets
import json

async def test_id():
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
                        "id": "test",
                        "mode": "test",
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
            with open("test_result.txt", "w") as f:
                f.write(res)
    except Exception as e:
        with open("test_result.txt", "w") as f:
            f.write(str(e))

asyncio.run(test_id())
