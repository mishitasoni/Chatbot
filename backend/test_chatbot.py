from dotenv import load_dotenv
load_dotenv()

from app.services.chatbot import ask_llm

while True:
    question = input("You: ")

    if question.lower() == "exit":
        break

    answer = ask_llm(question)

    print()
    print("Bot:", answer)
    print()