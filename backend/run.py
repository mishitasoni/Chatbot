import subprocess
import sys
import os
import uvicorn
import signal

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    node_dir = os.path.join(backend_dir, "whatsapp-service")
    
    print("Starting Node.js WhatsApp service...")
    # Start Node process
    node_process = subprocess.Popen(
        ["node", "index.js"], 
        cwd=node_dir, 
        shell=True
    )
    
    def cleanup(signum, frame):
        print("\nShutting down Node.js service...")
        node_process.terminate()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("Initializing database tables...")
    subprocess.run([sys.executable, "-m", "app.database.create_tables"], check=True)
    
    print("Starting FastAPI Backend...")
    try:
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
    except KeyboardInterrupt:
        pass
    finally:
        print("Cleaning up Node.js process...")
        node_process.terminate()
        try:
            node_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            node_process.kill()

if __name__ == "__main__":
    main()
