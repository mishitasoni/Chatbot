import sqlite3

uri = r"file:C:/Users/mishs/.openclaw/state/openclaw.sqlite?mode=ro"
try:
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    schema = conn.execute("PRAGMA table_info(channel_ingress_events)").fetchall()
    with open('schema_channel_ingress_events.txt', 'w') as f:
        f.write(str(schema))
    
    rows = conn.execute("SELECT * FROM channel_ingress_events ORDER BY rowid DESC LIMIT 3").fetchall()
    with open('rows_channel_ingress_events.txt', 'w') as f:
        f.write(str(rows))
except Exception as e:
    print("Error:", e)
