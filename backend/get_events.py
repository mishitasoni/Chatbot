import json

events = set()
with open("e:/Chatbot/backend/openclaw_debug2.log", "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            if "event" in data:
                events.add(data["event"])
        except:
            pass
            
with open("e:/Chatbot/backend/events.txt", "w", encoding="utf-8") as out:
    out.write(", ".join(events))
