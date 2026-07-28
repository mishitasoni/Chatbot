import sqlite3
import os
import traceback
import json

home = os.path.expanduser("~")
db_path = os.path.join(home, ".openclaw", "state", "openclaw.sqlite")

with open(r"e:\Chatbot\db_out.txt", "w") as f:
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        
        tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        f.write("Tables: " + str(tables) + "\n\n")
        
        if ("channel_pairing_requests",) in tables:
            rows = con.execute("SELECT * FROM channel_pairing_requests ORDER BY rowid DESC LIMIT 5").fetchall()
            f.write("channel_pairing_requests: " + str(rows) + "\n")
            
        if ("device_pairing_pending",) in tables:
            rows = con.execute("SELECT * FROM device_pairing_pending ORDER BY rowid DESC LIMIT 5").fetchall()
            f.write("device_pairing_pending: " + str(rows) + "\n")
            
    except Exception as e:
        f.write("Error: " + str(e) + "\n" + traceback.format_exc())
