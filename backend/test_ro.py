import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('file:///C:/Users/mishs/.openclaw/state/openclaw.sqlite?mode=ro', uri=True)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    print("Tables:")
    print(tables)
    
    if 'messages' in tables['name'].values:
        print("\nMessages Schema:")
        schema = pd.read_sql("PRAGMA table_info(messages)", conn)
        print(schema)
        
    elif 'message' in tables['name'].values:
        print("\nMessage Schema:")
        schema = pd.read_sql("PRAGMA table_info(message)", conn)
        print(schema)
        
except Exception as e:
    print(f"Error: {e}")
