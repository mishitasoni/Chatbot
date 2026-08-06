FROM python:3.10-bookworm

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs



WORKDIR /app

COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

COPY backend/whatsapp-service/package*.json ./backend/whatsapp-service/
RUN cd backend/whatsapp-service && npm install

COPY backend/requirements.txt ./backend/
RUN cd backend && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN cd frontend && npm run build

EXPOSE 7860

RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
