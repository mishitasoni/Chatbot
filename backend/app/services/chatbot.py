import os
import re
from mistralai.client import Mistral

def ask_llm(question: str):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return "Error: Mistral API key not found in environment."
    client = Mistral(api_key=api_key)
    
    try:
        # Extract image if present
        img_match = re.search(r'!\[.*?\]\((data:image/.*?;base64,[^)]+)\)', question)
        
        if img_match:
            image_url = img_match.group(1)
            # Remove image markdown from question for the text prompt
            text_only = re.sub(r'!\[.*?\]\((data:image/.*?;base64,[^)]+)\)', '', question).strip()
            
            response = client.chat.complete(
                model="pixtral-12b-2409",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text_only if text_only else "Analyze this image. If it contains a question, math problem, or puzzle, please solve it and explain the solution. If not, describe what is in the image in detail."},
                            {"type": "image_url", "image_url": image_url}
                        ]
                    }
                ]
            )
        else:
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "user", "content": question}
                ]
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"