import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:060805@localhost:5432/chatbot_db")
    cur = conn.cursor()
    cur.execute("SELECT id, telegram_bot_token FROM users")
    rows = cur.fetchall()
    for r in rows:
        print(r)
    cur.close()
    conn.close()
except Exception as e:
    print(e)
