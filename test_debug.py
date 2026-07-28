import urllib.request
import json
try:
    req = urllib.request.Request("http://localhost:8000/api/integrations/debug_db", headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    print(response.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
