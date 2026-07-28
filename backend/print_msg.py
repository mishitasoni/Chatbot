import json

with open("e:/Chatbot/backend/openclaw_debug2.log", "r", encoding="utf-8") as f, open("e:/Chatbot/backend/sample.json", "w", encoding="utf-8") as out:
    for line in f:
        try:
            data = json.loads(line)
            if data.get("event") == "session.message":
                out.write(json.dumps(data, indent=2))
                break
        except:
            pass
