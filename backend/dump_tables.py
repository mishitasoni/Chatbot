import sqlite3

try:
    uri = r"file:C:/Users/mishs/.openclaw/state/openclaw.sqlite?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    tables = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall()
    
    with open('tables.txt', 'w', encoding='utf-8') as f:
        for t in tables:
            f.write(f"Table: {t[0]}\nSQL: {t[1]}\n\n")
            
    print("Successfully wrote tables.txt")
except Exception as e:
    print(f"Error: {e}")
