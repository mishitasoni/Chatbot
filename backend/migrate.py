import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:060805@localhost:5432/chatbot_db")
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN telegram_bot_token VARCHAR(255);")
    cur.execute("ALTER TABLE users ADD COLUMN whatsapp_session_data VARCHAR(1000);")
    conn.commit()
    cur.close()
    conn.close()
    print("Migration successful")
except Exception as e:
    print(f"Migration error: {e}")
