const express = require('express');
const cors = require('cors');
const qrcode = require('qrcode');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, downloadMediaMessage } = require('@whiskeysockets/baileys');
const pino = require('pino');

const app = express();
app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
    res.send('WhatsApp Microservice is running successfully!');
});

const PORT = 3001;
const FASTAPI_PORT = process.env.PORT || 10000;
const FASTAPI_WEBHOOK_URL = `http://127.0.0.1:${FASTAPI_PORT}/whatsapp/webhook/node`;
const FASTAPI_STATUS_URL = `http://127.0.0.1:${FASTAPI_PORT}/integrations/channels/whatsapp/status`;
const SESSIONS_DIR = path.join(__dirname, '.wwebjs_auth');

const activeSessions = new Map();

async function initWhatsAppSession(userId) {
    const userIdStr = String(userId);

    if (activeSessions.has(userIdStr)) {
        return activeSessions.get(userIdStr);
    }

    console.log(`[WhatsApp Service] Initializing session for User ${userIdStr}...`);

    const sessionDir = path.join(SESSIONS_DIR, `session-user_${userIdStr}`);
    
    // Baileys multi-file auth state
    const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
    const { version, isLatest } = await fetchLatestBaileysVersion();
    console.log(`using WA v${version.join('.')}, isLatest: ${isLatest}`);

    const sessionObj = {
        userId: userIdStr,
        connected: false,
        qrBase64: null,
        sock: null,
        botSentMessageIds: new Set(),
        recentBotResponses: new Set()
    };
    activeSessions.set(userIdStr, sessionObj);

    const startSock = () => {
        const sock = makeWASocket({
            version,
            logger: pino({ level: 'silent' }),
            printQRInTerminal: false,
            auth: state,
            generateHighQualityLinkPreview: true,
            getMessage: async (key) => {
                return { conversation: 'hello' }
            }
        });

        sessionObj.sock = sock;

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            if (qr) {
                try {
                    sessionObj.qrBase64 = await qrcode.toDataURL(qr);
                    sessionObj.connected = false;
                    console.log(`[WhatsApp Service] Generated QR Code for User ${userIdStr}`);
                } catch (err) {
                    console.error(`[WhatsApp QR Error]:`, err);
                }
            }
            
            if (connection === 'close') {
                const shouldReconnect = (lastDisconnect.error)?.output?.statusCode !== DisconnectReason.loggedOut;
                console.log(`[WhatsApp Service] User ${userIdStr} connection closed due to`, lastDisconnect.error, ', reconnecting:', shouldReconnect);
                
                sessionObj.connected = false;
                
                if (shouldReconnect) {
                    startSock();
                } else {
                    activeSessions.delete(userIdStr);
                    try {
                        fs.rmSync(sessionDir, { recursive: true, force: true });
                    } catch(e){}
                }
                
                // Notify backend
                try {
                    await axios.post(FASTAPI_STATUS_URL, {
                        user_id: parseInt(userIdStr),
                        status: 'disconnected',
                        phone_number: null
                    });
                } catch(e) {}
            } else if (connection === 'open') {
                console.log(`[WhatsApp Service] User ${userIdStr} connected successfully!`);
                sessionObj.connected = true;
                sessionObj.qrBase64 = null;
                
                const myNumber = sock.user.id.split(':')[0];
                try {
                    await axios.post(FASTAPI_STATUS_URL, {
                        user_id: parseInt(userIdStr),
                        status: 'connected',
                        phone_number: myNumber
                    });
                } catch(e) {
                    console.error('[WhatsApp Service] Error syncing status:', e.message);
                }
            }
        });

        sock.ev.on('messages.upsert', async (m) => {
            if (m.type !== 'notify' && m.type !== 'append') return;
            for (const msg of m.messages) {
                const remoteJid = msg.key.remoteJid;
                if (!remoteJid) continue;

                // Determine our own Number safely
                let isMessageYourself = false;
                let myNumber = "";
                let remoteNumber = "";
                if (sock.user && sock.user.id) {
                    myNumber = sock.user.id.split(':')[0];
                    remoteNumber = remoteJid.split('@')[0];
                    isMessageYourself = (myNumber === remoteNumber);
                }

                // Log every message to see what we are getting!
                console.log(`[DEBUG] Received msg. fromMe: ${msg.key.fromMe}, remoteJid: ${remoteJid}, isYourself: ${isMessageYourself}`);

                // Prevent infinite loop by ignoring messages the bot just sent
                if (msg.key.id && sessionObj.botSentMessageIds.has(msg.key.id)) continue;
                
                // Allow ONLY messages where either:
                // 1. It is sent to yourself (personal chat)
                // 2. OR it is an explicit direct message to the bot's number from someone else
                // But for now, let's process personal chats.
                if (!isMessageYourself) {
                    continue;
                }
                
                let msgContent = msg.message;
                if (msgContent?.ephemeralMessage?.message) {
                    msgContent = msgContent.ephemeralMessage.message;
                } else if (msgContent?.viewOnceMessage?.message) {
                    msgContent = msgContent.viewOnceMessage.message;
                } else if (msgContent?.viewOnceMessageV2?.message) {
                    msgContent = msgContent.viewOnceMessageV2.message;
                } else if (msgContent?.documentWithCaptionMessage?.message) {
                    msgContent = msgContent.documentWithCaptionMessage.message;
                }
                
                let body = msgContent?.conversation || 
                           msgContent?.extendedTextMessage?.text || 
                           msgContent?.imageMessage?.caption || 
                           msgContent?.videoMessage?.caption || 
                           "";
                           
                if (!body) {
                    // Ignore protocol messages in logs to avoid spam
                    if (!msgContent?.protocolMessage) {
                        console.log(`[WhatsApp Service] Empty body detected. Message structure:`, JSON.stringify(msg.message));
                    }
                } else {
                    console.log(`[WhatsApp Service] Processing message from ${remoteJid}: ${body}`);
                }
                
                let base64Media = null;
                let mimeType = null;
                
                if (msg.message?.imageMessage || msg.message?.videoMessage || msg.message?.documentMessage) {
                    try {
                        const buffer = await downloadMediaMessage(msg, 'buffer', { }, { logger: pino({ level: 'silent' }) });
                        base64Media = buffer.toString('base64');
                        if (msg.message?.imageMessage) mimeType = msg.message.imageMessage.mimetype;
                        else if (msg.message?.videoMessage) mimeType = msg.message.videoMessage.mimetype;
                        else if (msg.message?.documentMessage) mimeType = msg.message.documentMessage.mimetype;
                    } catch (e) {
                        console.error('[WhatsApp Service] Error downloading media:', e);
                        body = "[Media Download Failed] " + body;
                    }
                }

                try {
                    await axios.post(FASTAPI_WEBHOOK_URL, {
                        userId: userIdStr,
                        from: remoteJid.replace('@s.whatsapp.net', '@c.us'),
                        body: body,
                        mediaBase64: base64Media,
                        mimeType: mimeType
                    }, {
                        maxContentLength: Infinity,
                        maxBodyLength: Infinity
                    });
                } catch (error) {
                    console.error(`[WhatsApp Service] Error forwarding webhook:`, error.message);
                }
            }
        });
    };

    startSock();
    return sessionObj;
}

app.get('/qr/:userId', async (req, res) => {
    const userId = req.params.userId;
    const sessionObj = await initWhatsAppSession(userId);

    if (sessionObj.connected) {
        return res.json({ status: 'connected', message: 'Already connected' });
    }
    
    if (sessionObj.qrBase64) {
        return res.json({ status: 'loading', qr: sessionObj.qrBase64 });
    }
    
    return res.json({ status: 'loading', qr: 'LOADING...' });
});

app.post('/send', async (req, res) => {
    const { userId, to, message } = req.body;
    const userIdStr = String(userId);
    const sessionObj = activeSessions.get(userIdStr);

    if (!sessionObj || !sessionObj.connected || !sessionObj.sock) {
        return res.status(400).json({ error: 'Client not connected' });
    }

    try {
        let jid = to;
        if (jid.includes('@c.us')) {
            jid = jid.replace('@c.us', '@s.whatsapp.net');
        } else if (!jid.includes('@')) {
            jid = `${jid.replace('+', '')}@s.whatsapp.net`;
        }
        
        sessionObj.recentBotResponses.add(message);
        
        const sentMsg = await sessionObj.sock.sendMessage(jid, { text: message });
        
        if (sentMsg && sentMsg.key && sentMsg.key.id) {
            sessionObj.botSentMessageIds.add(sentMsg.key.id);
        }
        
        res.json({ success: true });
    } catch (error) {
        console.error(`[WhatsApp Service] Error sending message:`, error);
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`WhatsApp Microservice running on port ${PORT}`);
    
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
