import os
import subprocess
import sys
import threading
import platform

# 1. Install Node.js dependencies and build frontend
print("Building frontend...")
subprocess.run(["npm", "install"], cwd="frontend", check=True)
subprocess.run(["npm", "run", "build"], cwd="frontend", check=True)

# 2. Install Node.js dependencies for whatsapp-service
print("Installing whatsapp-service dependencies...")
subprocess.run(["npm", "install"], cwd="whatsapp-service", check=True)

# 3. Add backend path to sys.path so imports work correctly
sys.path.insert(0, os.path.abspath("backend"))

# 4. Start whatsapp node service in background
# (We don't need to do this here because FastAPI's startup event in main.py already does it!
# Wait, main.py does: `node_process = subprocess.Popen([node_cmd, "index.js"], cwd=whatsapp_dir, shell=False)`
# So we just need to let FastAPI start.)

# 5. Initialize Database tables
print("Initializing database tables...")
subprocess.run([sys.executable, "-m", "app.database.create_tables"], cwd="backend", check=True)

# 6. Expose the FastAPI app
# Hugging Face Gradio SDK will automatically run `uvicorn app.py:app --port 7860`
from backend.app.main import app
