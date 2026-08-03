FROM nikolaik/python-nodejs:python3.10-nodejs20

# Install required dependencies for Puppeteer/Chromium
RUN apt-get update \
    && apt-get install -y wget gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 \
      --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy whatsapp service and install dependencies
COPY whatsapp-service/package*.json ./whatsapp-service/
RUN cd whatsapp-service && npm install

# Copy backend and install dependencies
COPY backend/requirements.txt ./backend/
RUN cd backend && pip install --no-cache-dir -r requirements.txt

# Copy all the source code
COPY . .

# Expose the port for Render (Render injects $PORT environment variable)
EXPOSE 10000

# Make the start script executable
RUN chmod +x /app/start.sh

# Run the start script
CMD ["/app/start.sh"]
