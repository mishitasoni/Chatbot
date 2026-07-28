import sqlite3
try:
    conn = sqlite3.connect(r'C:\Users\mishs\.openclaw\state\openclaw.sqlite')
    tables = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall()
    with open('schema.txt', 'w') as f:
        for name, sql in tables:
            f.write(f"Table: {name}\nSQL: {sql}\n\n")
    print("Schema dumped successfully.")
except Exception as e:
    print(f"Error: {e}")
