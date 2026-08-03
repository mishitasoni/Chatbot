# Multi-Channel AI Chatbot Platform

A comprehensive multi-channel AI chatbot platform that integrates with various messaging services like Telegram and WhatsApp, powered by a Python backend and a React dashboard.

## Project Structure

This project is organized into three main components:

### 1. Backend (`/backend`)
A robust Python-based API built with **FastAPI**. It handles the core logic, database interactions, AI model integrations, and messaging API webhooks.
- **Framework**: FastAPI
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **AI Integration**: Google Generative AI (Gemini), Mistral AI, Groq
- **Messaging Integrations**: pyTelegramBotAPI
- **Other tools**: JWT Auth, bcrypt, Uvicorn, ngrok/cloudflared for tunneling

### 2. Frontend (`/frontend`)
A modern, responsive web dashboard for managing the chatbot, viewing connected channels, and sending/receiving messages.
- **Framework**: React 19 with Vite
- **Styling**: Tailwind CSS & Framer Motion
- **Icons**: Lucide React & React Icons
- **Markdown**: react-markdown with remark/rehype plugins for rendering AI responses

### 3. WhatsApp Service (`/whatsapp-service`)
A dedicated Node.js microservice to handle WhatsApp Web integration.
- **Framework**: Express.js
- **WhatsApp Client**: whatsapp-web.js (uses Puppeteer)
- **Features**: Generates QR codes for authentication and handles WhatsApp messaging events.

## Getting Started

### Prerequisites
- Node.js & npm (for Frontend and WhatsApp Service)
- Python 3.9+ (for Backend)

### Installation & Running

#### Backend
1. Navigate to the backend directory: `cd backend`
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the server: `uvicorn app.main:app --reload` (or your specific start command)

#### Frontend
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start the development server: `npm run dev`

#### WhatsApp Service
1. Navigate to the whatsapp-service directory: `cd whatsapp-service`
2. Install dependencies: `npm install`
3. Start the service: `node index.js`

## Architecture Overview
- The **Frontend** communicates with the **Backend** via REST APIs and WebSockets.
- The **Backend** handles AI processing and stores message history. It natively connects to APIs like Telegram.
- The **WhatsApp Service** acts as a bridge for WhatsApp. It communicates with the **Backend** to forward incoming WhatsApp messages and to receive/send outbound responses.
