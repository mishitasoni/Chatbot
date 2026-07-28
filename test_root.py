import urllib.request
import traceback

try:
    response = urllib.request.urlopen("http://localhost:8000/")
    print("Status:", response.status)
    print(response.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
