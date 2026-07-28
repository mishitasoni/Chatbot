import shutil
import os
import sqlite3

src_dir = r'C:\Users\mishs\.openclaw\state'
dst_dir = r'e:\Chatbot\backend\tmp_db'

if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)

for file in ['openclaw.sqlite', 'openclaw.sqlite-wal', 'openclaw.sqlite-shm']:
    src_file = os.path.join(src_dir, file)
    if os.path.exists(src_file):
        shutil.copy2(src_file, os.path.join(dst_dir, file))

try:
    conn = sqlite3.connect(os.path.join(dst_dir, 'openclaw.sqlite'))
    tables = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall()
    with open('schema.txt', 'w') as f:
        for name, sql in tables:
            f.write(f"Table: {name}\nSQL: {sql}\n\n")
    print("Schema dumped successfully from copy.")
except Exception as e:
    print(f"Error: {e}")
