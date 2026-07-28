import sqlite3
import json
import os
import traceback

home = os.path.expanduser("~")
db_path = os.path.join(home, ".openclaw", "state", "openclaw.sqlite")

output_path = r'e:\Chatbot\out2.txt'

with open(output_path, 'w', encoding='utf-8') as f:
    try:
        f.write(f"DB Path: {db_path}\n")
        if not os.path.exists(db_path):
            f.write("ERROR: DB file does not exist!\n")
        else:
            con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            # Find the most recent delivery queue entries for whatsapp
            rows = con.execute("SELECT channel, entry_json FROM delivery_queue_entries ORDER BY rowid DESC LIMIT 10").fetchall()
            
            f.write(f"Found {len(rows)} rows\n\n")
            for row in rows:
                f.write(f"Channel: {row[0]}\n")
                f.write(f"Entry: {row[1]}\n")
                f.write("---\n")
            f.write("Success.\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
        f.write(traceback.format_exc())
