import sqlite3

try:
    print("Connecting to DB...")
    conn = sqlite3.connect(r'C:\Users\mishs\.openclaw\state\openclaw.sqlite', timeout=1.0)
    print("Connected.")
    cursor = conn.cursor()
    print("Executing query...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", tables)
except Exception as e:
    print("Error:", e)
