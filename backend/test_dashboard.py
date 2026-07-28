import urllib.request
import json

def fetch_dashboard():
    url = "http://127.0.0.1:18789/"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8')
            print(f"Status: {response.getcode()}")
            print("Content Snippet:")
            print(html[:1000])
    except Exception as e:
        print(f"Error fetching dashboard: {e}")

if __name__ == "__main__":
    fetch_dashboard()
