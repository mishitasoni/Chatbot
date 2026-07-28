import sqlite3
import json

db_path = r'C:\Users\mishs\.openclaw\state\openclaw.sqlite'
try:
    con = sqlite3.connect(db_path)
    rows = con.execute('SELECT channel, entry_json FROM delivery_queue_entries ORDER BY rowid DESC LIMIT 5').fetchall()
    for row in rows:
        print(f"Channel: {row[0]}")
        print(f"Entry: {row[1]}")
        print("---")
except Exception as e:
    print(f"Error: {e}")
