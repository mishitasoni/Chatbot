import urllib.request
try:
    response = urllib.request.urlopen("http://localhost:8000/api/integrations/whatsapp/qr/1")
    print(response.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
