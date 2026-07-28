"You are an AI Assistant connected via OpenClaw WhatsApp Gateway. Whenever a user sends a message on WhatsApp, forward the prompt to the custom API endpoint (http://localhost:8005/v1/chat/completions), passing the sender details as session_id: whatsapp_<phone_number> so the Web UI can display and track the WhatsApp conversation history in real time."

### Option 1: AI Prompt (To build or connect the codebase via AI Assistant)
If your friend is asking an AI Coding Assistant (like Gemini, ChatGPT, etc.) to integrate OpenClaw WhatsApp with her Web UI backend, she can use this prompt:

> *Prompt:*  
> "Create a full-stack application (FastAPI backend + React frontend) that connects an OpenClaw-integrated WhatsApp gateway to a Web UI dashboard. The backend should provide an OpenAI-compatible /v1/chat/completions endpoint so OpenClaw can forward WhatsApp messages to it. Parse incoming WhatsApp messages and sender phone numbers into session IDs (e.g., whatsapp_<phone_number>), store the messages in a database, query OpenClaw/AI for solutions, and display live WhatsApp chat history under a WhatsApp channel tab in the frontend UI."

---

### Option 2: OpenClaw Gateway Configuration Prompt
If she is configuring the system prompt inside *OpenClaw Gateway* so that WhatsApp messages route to her backend UI endpoint (http://localhost:8005/v1/chat/completions):

> *System Prompt / Instruction in OpenClaw:*  
> "You are an AI Assistant connected via OpenClaw WhatsApp Gateway. Whenever a user sends a message on WhatsApp, forward the prompt to the custom API endpoint (http://localhost:8005/v1/chat/completions), passing the sender details as session_id: whatsapp_<phone_number> so the Web UI can display and track the WhatsApp conversation history in real time."

---

### Key Architecture Checklist to Share with Her

1. *OpenClaw Gateway*: Running locally (default: http://127.0.0.1:18789) with the WhatsApp account linked.
2. *FastAPI Backend*: Running on port 8005 exposing:
   - `/v1/chat/completions` (Receives OpenClaw/WhatsApp payload & saves messages to DB)
   - `/api/chat/history/{session_id}` (Fetches conversation for UI)
3. *React Frontend*: Filter chats by channel WhatsApp to view live conversations linked to numbers like `whatsapp_+1234567890`.
