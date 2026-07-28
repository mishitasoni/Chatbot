import shutil
import sys

source = r'C:\Users\mishs\.gemini\antigravity-ide\brain\e2bf00dc-b46b-4fd5-bd5c-2423d73be392\.system_generated\tasks\task-356.log'
target = r'e:\Chatbot\backend\task_356_copy.txt'

try:
    shutil.copyfile(source, target)
    print("Copied successfully.")
except Exception as e:
    print(f"Error copying: {e}")
