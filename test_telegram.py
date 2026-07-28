import urllib.request
import urllib.parse
import json
import traceback

data = json.dumps({"user_id": 1, "token": "8956412686:AAG-Ws31xfuGcArKH-fake-test"}).encode('utf-8')
req = urllib.request.Request(
    "http://localhost:8000/api/integrations/telegram",
    data=data,
    headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
)

with open(r'e:\Chatbot\telegram_out2.txt', 'w', encoding='utf-8') as f:
    try:
        response = urllib.request.urlopen(req)
        f.write(f"Status: {response.status}\n")
        f.write(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        f.write(f"HTTPError: {e.code}\n")
        f.write(e.read().decode('utf-8'))
    except Exception as e:
        f.write(f"Error: {e}\n")
        f.write(traceback.format_exc())
