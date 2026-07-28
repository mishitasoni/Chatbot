import sqlite3

uri = r"file:C:/Users/mishs/.openclaw/state/openclaw.sqlite?mode=ro"
try:
    conn = sqlite3.connect(uri, uri=True)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("Tables:", tables)
except Exception as e:
    print("Error:", e)
