import os
import telebot
from dotenv import load_dotenv

load_dotenv()

# Import your existing Gemini chatbot logic
from app.services.chatbot import ask_llm

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN is not set in .env")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

print("========================================")
print(" Telegram Bot is running! ")
print(" Waiting for messages... ")
print("========================================")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    question = message.text
    
    # 1. Print the user's message in the terminal
    print(f"\nYou: {question}")
    
    try:
        import requests
        gateway_url = os.getenv("OPENCLAW_GATEWAY_URL")
        token = os.getenv("OPENCLAW_GATEWAY_TOKEN")
        
        if not gateway_url:
            raise Exception("OPENCLAW_GATEWAY_URL is not set in .env")

        payload = {
            "message": question,
            "from": str(message.from_user.id),
            "channel": "telegram"
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 2. Forward the message to OpenClaw
        response = requests.post(gateway_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            answer = response.json().get("message", "Sorry, no response from OpenClaw.")
        else:
            answer = f"Error from OpenClaw: {response.status_code} {response.text}"
        
        # 3. Print the bot's answer in the terminal
        print(f"\nBot: {answer}\n")
        
        # 4. Send the answer back to Telegram
        # Telegram has a 4096 character limit per message
        max_length = 4000
        if len(answer) > max_length:
            for i in range(0, len(answer), max_length):
                bot.reply_to(message, answer[i:i+max_length])
        else:
            bot.reply_to(message, answer)
        
    except Exception as e:
        error_msg = f"Sorry, an error occurred: {str(e)}"
        print(f"\nBot Error: {error_msg}\n")
        bot.reply_to(message, error_msg)

if __name__ == "__main__":
    bot.infinity_polling()
