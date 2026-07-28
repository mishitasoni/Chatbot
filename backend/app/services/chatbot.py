import os
from mistralai.client import Mistral

def ask_llm(question: str):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return "Error: Mistral API key not found in environment."
    client = Mistral(api_key=api_key)
    
    try:
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"