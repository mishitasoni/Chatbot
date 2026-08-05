const express = require('express');
const cors = require('cors');
const qrcode = require('qrcode');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const { Client, LocalAuth } = require('whatsapp-web.js');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 3001;
const FASTAPI_PORT = process.env.PORT || 10000;
const FASTAPI_WEBHOOK_URL = `http://127.0.0.1:${FASTAPI_PORT}/whatsapp/webhook/node`;
const SESSIONS_DIR = path.join(__dirname, '.wwebjs_auth');

function getBrowserPath() {
    const paths = [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        '/usr/bin/chromium',
        '/usr/bin/google-chrome'
    ];
    for (let p of paths) {
        if (fs.existsSync(p)) return p;
    }
    return process.env.PUPPETEER_EXECUTABLE_PATH || null;
}

const activeSessions = new Map();

async function initWhatsAppSession(userId) {
    const userIdStr = String(userId);

    if (activeSessions.has(userIdStr)) {
        return activeSessions.get(userIdStr);
    }

    console.log(`[WhatsApp Service] Initializing session for User ${userIdStr}...`);

    const puppeteerOptions = {
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-dev-shm-usage', 
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-extensions',
            '--disable-site-isolation-trials'
        ],
        timeout: 120000 // 120 seconds for slow Render servers
    };
    const browserPath = getBrowserPath();
    if (browserPath) puppeteerOptions.executablePath = browserPath;

    const client = new Client({
        authStrategy: new LocalAuth({ clientId: `user_${userIdStr}` }),
        puppeteer: puppeteerOptions,
        authTimeoutMs: 120000,
        qrMaxRetries: 5,
        webVersionCache: {
            type: 'none'
        }
    });

    const sessionObj = {
        userId: userIdStr,
        connected: false,
        qrBase64: null,
        client: client,
        botSentMessageIds: new Set(),
        recentBotResponses: new Set()
    };

    activeSessions.set(userIdStr, sessionObj);

    client.on('loading_screen', (percent, message) => {
        console.log(`[WhatsApp Service] User ${userIdStr} LOADING SCREEN`, percent, message);
    });

    client.on('auth_failure', (msg) => {
        console.error(`[WhatsApp Service] User ${userIdStr} AUTH FAILURE`, msg);
    });

    client.on('qr', async (qr) => {
        try {
            sessionObj.qrBase64 = await qrcode.toDataURL(qr);
            sessionObj.connected = false;
            console.log(`[WhatsApp Service] Generated QR Code for User ${userIdStr}`);
        } catch (err) {
            console.error(`[WhatsApp QR Error]:`, err);
        }
    });

    client.on('ready', () => {
        sessionObj.connected = true;
        sessionObj.qrBase64 = null;
        console.log(`[WhatsApp Service] User ${userIdStr} connected successfully!`);
    });

    client.on('disconnected', (reason) => {
        console.log(`[WhatsApp Service] User ${userIdStr} disconnected:`, reason);
        sessionObj.connected = false;
        activeSessions.delete(userIdStr);
    });

    // 4. 'Message Yourself' Architecture & 5. Anti-Infinite-Loop Safeguards
    client.on('message_create', async (msg) => {
        // Only process messages sent BY ME (Message Yourself)
        if (!msg.fromMe) return;
        
        console.log(`[DEBUG] fromMe Message: body="${msg.body}", to="${msg.to}", from="${msg.from}", _serialized="${client.info.wid._serialized}"`);

        // Ignore messages sent by the bot itself to prevent infinite loops
        if (sessionObj.botSentMessageIds.has(msg.id.id)) return;
        if (sessionObj.recentBotResponses.has(msg.body)) return;

        // Ensure the message is actually sent in our "Message Yourself" chat
        // WhatsApp sometimes routes self-chats using your internal @lid instead of your phone number.
        // To safely distinguish YOUR @lid from a FRIEND'S @lid, we verify the contact's isMe flag.
        try {
            const myNumber = client.info.wid.user + '@c.us';
            if (msg.to !== myNumber && msg.to !== client.info.wid._serialized && msg.to !== msg.from) {
                // If it doesn't strictly match our phone number, verify if the recipient contact is US
                const contact = await client.getContactById(msg.to);
                if (!contact || !contact.isMe) return;
            }
        } catch (e) {
            console.error('[WhatsApp Service] Error verifying contact:', e);
            return;
        }

        console.log(`[WhatsApp Service] Received message to self: ${msg.body}`);

        try {
            let base64Media = null;
            let mimeType = null;
            if (msg.hasMedia) {
                console.log('[WhatsApp Service] Message has media. Attempting to download...');
                try {
                    let media = null;
                    for (let attempt = 0; attempt < 10; attempt++) {
                        try {
                            media = await msg.downloadMedia();
                            if (media) break;
                        } catch (e) {
                            console.log(`[WhatsApp Service] Media download attempt ${attempt + 1} failed, retrying in 2s...`);
                            await new Promise(r => setTimeout(r, 2000));
                        }
                    }
                    
                    if (media) {
                        console.log(`[WhatsApp Service] Media downloaded successfully. Mimetype: ${media.mimetype}`);
                        if (media.mimetype.startsWith('image/')) {
                            base64Media = media.data;
                            mimeType = media.mimetype;
                        } else {
                            console.log(`[WhatsApp Service] Ignored non-image media: ${media.mimetype}`);
                        }
                    } else {
                        console.log('[WhatsApp Service] Media download returned null/undefined after 3 attempts.');
                        msg.body = "[Media Download Failed in Node] " + msg.body;
                    }
                } catch (err) {
                    console.error('[WhatsApp Service] Error downloading media:', err.message);
                    msg.body = "[Media Error in Node: " + err.message + "] " + msg.body;
                }
            } else {
                console.log('[WhatsApp Service] Message does NOT have media.');
            }

            // Forward message to FastAPI Webhook
            await axios.post(FASTAPI_WEBHOOK_URL, {
                userId: userIdStr,
                from: msg.from,
                body: msg.body,
                mediaBase64: base64Media,
                mimeType: mimeType
            }, {
                maxContentLength: Infinity,
                maxBodyLength: Infinity
            });
        } catch (error) {
            console.error(`[WhatsApp Service] Error forwarding webhook to FastAPI:`, error.message);
            // Fallback: send without media if it failed due to size
            try {
                await axios.post(FASTAPI_WEBHOOK_URL, {
                    userId: userIdStr,
                    from: msg.from,
                    body: "[Webhook Axios Error: " + error.message + "] " + msg.body
                });
            } catch (e2) {}
        }
    });

    client.initialize().catch(err => {
        console.error(`[WhatsApp Init Error]:`, err);
        activeSessions.delete(userIdStr);
    });

    return sessionObj;
}

app.get('/qr/:userId', async (req, res) => {
    const userId = req.params.userId;
    const sessionObj = await initWhatsAppSession(userId);

    if (sessionObj.connected) {
        console.log(`[WhatsApp Service] Returning CONNECTED for User ${userId}`);
        return res.json({ status: 'connected', message: 'Already connected' });
    }
    
    if (sessionObj.qrBase64) {
        console.log(`[WhatsApp Service] Returning QR for User ${userId}, length: ${sessionObj.qrBase64.length}`);
        return res.json({ status: 'loading', qr: sessionObj.qrBase64 });
    }
    
    console.log(`[WhatsApp Service] Returning LOADING... for User ${userId}`);
    return res.json({ status: 'loading', qr: 'LOADING...' });
});


app.post('/send', async (req, res) => {
    const { userId, to, message } = req.body;
    const userIdStr = String(userId);
    const sessionObj = activeSessions.get(userIdStr);

    if (!sessionObj || !sessionObj.connected) {
        return res.status(400).json({ error: 'Client not connected' });
    }

    try {
        let chatId = to;
        if (!chatId.includes('@')) {
            chatId = `${chatId.replace('+', '')}@c.us`;
        }
        
        // Anti-Infinite-Loop Safeguards
        sessionObj.recentBotResponses.add(message);
        
        const sentMsg = await sessionObj.client.sendMessage(chatId, message);
        
        if (sentMsg && sentMsg.id && sentMsg.id.id) {
            sessionObj.botSentMessageIds.add(sentMsg.id.id);
        }
        
        res.json({ success: true });
    } catch (error) {
        console.error(`[WhatsApp Service] Error sending message:`, error);
        res.status(500).json({ error: error.message });
    }
});

process.on('uncaughtException', (err) => {
    console.error('[WhatsApp UncaughtException]:', err.message || err);
});

process.on('unhandledRejection', (err) => {
    console.error('[WhatsApp UnhandledRejection]:', err.message || err);
});

app.listen(PORT, () => {
    console.log(`WhatsApp Microservice running on port ${PORT}`);
    
    // Auto-load existing sessions on startup
    try {
        if (fs.existsSync(SESSIONS_DIR)) {
            const sessionDirs = fs.readdirSync(SESSIONS_DIR);
            for (const dir of sessionDirs) {
                if (dir.startsWith('session-user_')) {
                    const userId = dir.replace('session-user_', '');
                    console.log(`[WhatsApp Service] Auto-restoring session for User ${userId}...`);
                    initWhatsAppSession(userId).catch(e => console.error(e));
                }
            }
        }
    } catch (err) {
        console.error(`[WhatsApp Service] Error auto-loading sessions:`, err);
    }
});
