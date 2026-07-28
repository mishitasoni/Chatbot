import subprocess
import threading
import time
import os
import re

active_whatsapp_processes = {}
qr_codes = {}

def get_qr_for_user(user_id: int):
    """
    Attempts to start a whatsapp linking process for the user.
    Since OpenClaw might be a single-tenant daemon, this is a best-effort 
    approach to grab the QR code string from stdout.
    """
    # If we already have a QR code generated and waiting
    if user_id in qr_codes:
        return qr_codes[user_id]
        
    # If a process is already running, wait a bit
    if user_id in active_whatsapp_processes:
        return None
        
    # Start a new process
    def run_openclaw_qr():
        try:
            # Use openclaw.cmd directly instead of npx
            cmd = ["openclaw.cmd", "channels", "login", "--channel", "whatsapp"]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            active_whatsapp_processes[user_id] = process
            
            # Read output to find QR code
            qr_lines = []
            capturing_qr = False
            for line in iter(process.stdout.readline, ''):
                print(f"[WhatsApp Worker {user_id}] {line.strip()}")
                
                if "1@" in line and len(line) > 50:
                    match = re.search(r'(1@[a-zA-Z0-9+/=,\-]+)', line)
                    if match:
                        qr_codes[user_id] = match.group(1)
                        break
                        
                # qrcode-terminal characters
                if '▄' in line or '█' in line or '▀' in line:
                    capturing_qr = True
                    qr_lines.append(line.replace('\n', '').replace('\r', ''))
                elif capturing_qr:
                    # If we were capturing and hit a line without blocks, we might be done.
                    # Usually there are empty lines before/after, but let's just collect all blocks.
                    pass
            
            if qr_lines and user_id not in qr_codes:
                qr_codes[user_id] = "\n".join(qr_lines)
                        
            # After getting QR, wait for process to finish
            process.wait()
            
            if user_id in active_whatsapp_processes:
                del active_whatsapp_processes[user_id]
                
        except Exception as e:
            print(f"[WhatsApp Manager] Error starting QR generation for {user_id}: {e}")
            if user_id in active_whatsapp_processes:
                del active_whatsapp_processes[user_id]

    thread = threading.Thread(target=run_openclaw_qr, daemon=True)
    thread.start()
    
    # Return placeholder if we just started
    return "LOADING..."
