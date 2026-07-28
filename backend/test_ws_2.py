import asyncio
import websockets

async def test():
    urls = [
        'ws://127.0.0.1:18789/', 
        'ws://127.0.0.1:18789/ws', 
        'ws://127.0.0.1:18789/events',
        'ws://127.0.0.1:18789/api/v1/events',
        'ws://127.0.0.1:18789/api/v1/ws',
        'ws://127.0.0.1:18789/api/events',
        'ws://127.0.0.1:18789/v1/events'
    ]
    headers = {'Authorization': 'Bearer 140ea20c62a26b8a4f8ba257f1747f213e27b139ae654920'}
    
    with open("ws_test_out.txt", "w") as f:
        for u in urls:
            try:
                f.write(f'Trying {u}\n')
                async with websockets.connect(u, additional_headers=headers, open_timeout=2) as ws:
                    f.write(f'Success: {u}\n')
            except Exception as e:
                f.write(f'Failed: {u} {type(e)}\n')

asyncio.run(test())
