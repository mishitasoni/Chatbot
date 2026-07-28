import urllib.request
try:
    req = urllib.request.Request("http://127.0.0.1:18789/openapi.json")
    res = urllib.request.urlopen(req)
    with open("e:\\Chatbot\\openclaw_api.json", "w") as f:
        f.write(res.read().decode())
except Exception as e:
    with open("e:\\Chatbot\\openclaw_api.json", "w") as f:
        f.write(str(e))
