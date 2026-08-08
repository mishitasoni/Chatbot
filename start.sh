#!/bin/bash

# Start the WhatsApp Node.js microservice in the background
echo "Starting WhatsApp Microservice..."
cd /app/backend
node whatsapp_service.js &

# Start the FastAPI backend in the foreground
echo "Starting FastAPI Backend..."
cd /app/backend

# Initialize database tables (creates them if they don't exist)
echo "Initializing database tables..."
python -m app.database.create_tables

# HF Spaces automatically injects the PORT environment variable as 7860. We default to 7860 if not set.
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}
