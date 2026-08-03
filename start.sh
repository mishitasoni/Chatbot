#!/bin/bash

# Start the WhatsApp Node.js microservice in the background
echo "Starting WhatsApp Microservice..."
cd /app/whatsapp-service
node index.js &

# Start the FastAPI backend in the foreground
echo "Starting FastAPI Backend..."
cd /app/backend
# Render automatically injects the PORT environment variable. We default to 10000 if not set.
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
