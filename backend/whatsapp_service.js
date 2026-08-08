const express = require('express');
const cors = require('cors');
const qrcode = require('qrcode');
const path = require('path');
const fs = require('fs');
const pino = require('pino');
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, downloadMediaMessage } = require('@whiskeysockets/baileys');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.WHATSAPP_SERVICE_PORT || 8006;
const FASTAPI_URL = process.env.FASTAPI_URL || `http://127.0.0.1:${process.env.PORT || 7860}`;
const SESSIONS_DIR = path.join(__dirname, 'sessions');
const UPLOADS_DIR = path.join(__dirname, '..', 'uploads', 'images');

if (!fs.existsSync(SESSIONS_DIR)) {
  fs.mkdirSync(SESSIONS_DIR, { recursive: true });
}
if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

const activeSessions = new Map();

async function initWhatsAppSession(userId, forceRestart = false) {
  const userIdStr = String(userId || 1);
  const sessionPath = path.join(SESSIONS_DIR, `session-${userIdStr}`);

  if (forceRestart) {
    if (activeSessions.has(userIdStr)) {
      const s = activeSessions.get(userIdStr);
      try { s.client.end(new Error("Force Restart")); } catch (e) {}
      activeSessions.delete(userIdStr);
    }
    for (let i = 0; i < 5; i++) {
      try {
        if (fs.existsSync(sessionPath)) {
          fs.rmSync(sessionPath, { recursive: true, force: true });
        }
        break;
      } catch (e) {
        if (i === 4) console.log(`[WhatsApp-Web Service] Force restart could not remove directory:`, e.message);
        await new Promise(r => setTimeout(r, 1000));
      }
    }
  }

  if (activeSessions.has(userIdStr)) {
    const existing = activeSessions.get(userIdStr);
    if (!forceRestart && (existing.connected || existing.qrBase64)) {
      return existing;
    }
  }

  const { state, saveCreds } = await useMultiFileAuthState(sessionPath);

  const sessionObj = {
    userId: userIdStr,
    connected: false,
    phone: null,
    qrBase64: null,
    client: null, 
    connecting: true,
    error: null,
    botSentMessageIds: new Set(),
    recentBotResponses: new Set(),
    processedIncomingMsgIds: new Set()
  };

  activeSessions.set(userIdStr, sessionObj);

  const startSock = () => {
    const sock = makeWASocket({
      auth: state,
      printQRInTerminal: false,
      logger: pino({ level: "silent" }) // Prevents Baileys from spamming logs
    });

    sessionObj.client = sock;

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;
      
      if (qr) {
        try {
          const qrDataUrl = await qrcode.toDataURL(qr);
          sessionObj.qrBase64 = qrDataUrl;
          sessionObj.connected = false;
          console.log(`[WhatsApp-Web Service] Generated Fresh QR Code for User ${userIdStr}`);
        } catch (err) {
          console.error(`[WhatsApp-Web QR Error]:`, err);
        }
      }

      if (connection === 'close') {
        const shouldReconnect = (lastDisconnect.error)?.output?.statusCode !== DisconnectReason.loggedOut;
        console.log(`[WhatsApp-Web Service] User ${userIdStr} disconnected. Reconnect: ${shouldReconnect}`);
        
        sessionObj.connected = false;
        sessionObj.connecting = false;
        
        if (shouldReconnect) {
          startSock();
        } else {
           activeSessions.delete(userIdStr);
           try {
             if (fs.existsSync(sessionPath)) {
               fs.rmSync(sessionPath, { recursive: true, force: true });
             }
           } catch(e) {}
        }
      } else if (connection === 'open') {
        sessionObj.connected = true;
        sessionObj.qrBase64 = null;
        sessionObj.connecting = false;
        sessionObj.phone = sock.user.id ? sock.user.id.split(':')[0] : 'Connected';
        console.log(`[WhatsApp-Web Service] User ${userIdStr} connected successfully (+${sessionObj.phone})`);
      }
    });

    sock.ev.on('messages.upsert', async (m) => {
      if (m.type !== 'notify') return;
      
      for (const msg of m.messages) {
        // 1. Only process messages sent BY YOU (the user)
        if (!msg.key.fromMe) continue;
        if (!msg.message) continue;

        const myJid = sock.user.id.replace(/:\d+/, ''); // Clean JID format
        const remoteJid = msg.key.remoteJid;
        
        console.log(`[DEBUG] fromMe: ${msg.key.fromMe}, remoteJid: ${remoteJid}, myJid: ${myJid}`);
        
        // 2. Only process messages sent TO yourself
        const meLid = sock.authState?.creds?.me?.lid?.split(':')[0];
        const isSelfChat = remoteJid.includes(myJid.split('@')[0]) || (meLid && remoteJid.includes(meLid));
        if (!isSelfChat) {
            continue;
        }

        if (sessionObj.botSentMessageIds.has(msg.key.id)) continue;
        if (sessionObj.processedIncomingMsgIds.has(msg.key.id)) continue;

        sessionObj.processedIncomingMsgIds.add(msg.key.id);
        console.log(`[WhatsApp-Web Service] Received a message from self. Processing...`);

        const cleanPhone = myJid.split('@')[0];
        const sessionId = `whatsapp_${cleanPhone}`;

        try {
            const textMessage = msg.message.conversation || msg.message.extendedTextMessage?.text || msg.message.imageMessage?.caption || '';

            if (sessionObj.recentBotResponses.has(textMessage)) continue;

            let imageMessage = msg.message.imageMessage;
            let targetMsg = msg;
            
            // Check if the user replied to an image
            if (!imageMessage && msg.message.extendedTextMessage?.contextInfo?.quotedMessage?.imageMessage) {
                imageMessage = msg.message.extendedTextMessage.contextInfo.quotedMessage.imageMessage;
                // Create a pseudo-message for Baileys to download the quoted media
                targetMsg = {
                    key: {
                        remoteJid: remoteJid,
                        fromMe: msg.message.extendedTextMessage.contextInfo.participant === sock.user.id,
                        id: msg.message.extendedTextMessage.contextInfo.stanzaId,
                        participant: msg.message.extendedTextMessage.contextInfo.participant
                    },
                    message: msg.message.extendedTextMessage.contextInfo.quotedMessage
                };
            }

            let base64Media = null;
            let mimeType = null;
            
            if (imageMessage) {
                try {
                    const buffer = await downloadMediaMessage(
                        targetMsg,
                        'buffer',
                        { },
                        { 
                            logger: pino({ level: 'silent' }),
                            reuploadRequest: sock.updateMediaMessage
                        }
                    );
                    base64Media = buffer.toString('base64');
                    mimeType = imageMessage.mimetype || 'image/jpeg';
                } catch (downloadErr) {
                    console.error("[WhatsApp-Web Service] Media download failed:", downloadErr.message);
                }
            }
            
            try {
                await fetch(`${FASTAPI_URL}/whatsapp/webhook/node`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        userId: userIdStr,
                        from: remoteJid.replace('@s.whatsapp.net', '@c.us'),
                        body: textMessage,
                        mediaBase64: base64Media,
                        mimeType: mimeType,
                        fromMe: msg.key.fromMe,
                        isSelfChat: isSelfChat
                    })
                });
                console.log(`[WhatsApp-Web Service] Forwarded message to FastAPI Webhook`);
            } catch (err) {
                console.error(`[WhatsApp-Web Service] Error forwarding webhook:`, err.message);
            }
        } catch (err) {
            console.error(`[WhatsApp-Web Message Error]:`, err);
        }
      }
    });
  };

  startSock();
  return sessionObj;
}

// API Routes
app.post('/api/wa/send', async (req, res) => {
    const { userId, to, message } = req.body;
    const userIdStr = String(userId);
    const sessionObj = activeSessions.get(userIdStr);

    if (!sessionObj || !sessionObj.connected || !sessionObj.client) {
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
        
        const sentMsg = await sessionObj.client.sendMessage(jid, { text: message });
        
        if (sentMsg && sentMsg.key && sentMsg.key.id) {
            sessionObj.botSentMessageIds.add(sentMsg.key.id);
        }
        
        res.json({ success: true });
    } catch (error) {
        console.error(`[WhatsApp Service] Error sending message:`, error);
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/wa/qr', async (req, res) => {
  const userId = req.query.user_id || 1;
  const sessionObj = await initWhatsAppSession(userId, req.query.force === 'true');

  for (let i = 0; i < 40; i++) {
    if (sessionObj.qrBase64 || sessionObj.connected || sessionObj.error) break;
    await new Promise((r) => setTimeout(r, 500));
  }

  if (sessionObj.error) {
    return res.status(500).json({ error: sessionObj.error });
  }

  return res.json({
    qr_code: sessionObj.qrBase64,
    connected: sessionObj.connected,
    phone: sessionObj.phone,
    connecting: sessionObj.connecting
  });
});

app.get('/api/wa/status', async (req, res) => {
  const userId = req.query.user_id || 1;
  const userIdStr = String(userId);
  const sessionObj = activeSessions.get(userIdStr);

  if (!sessionObj) {
    return res.json({ connected: false, phone: 'Disconnected' });
  }

  return res.json({
    connected: sessionObj.connected,
    phone: sessionObj.phone || (sessionObj.connected ? 'Linked' : 'Disconnected'),
    qr_code: sessionObj.qrBase64,
    connecting: sessionObj.connecting
  });
});

app.post('/api/wa/logout', async (req, res) => {
  const userId = req.query.user_id || 1;
  const userIdStr = String(userId);

  if (activeSessions.has(userIdStr)) {
    const sessionObj = activeSessions.get(userIdStr);
    try {
      if (sessionObj.client) {
        sessionObj.client.logout();
      }
    } catch (e) {}
    activeSessions.delete(userIdStr);
  }

  const sessionPath = path.join(SESSIONS_DIR, `session-${userIdStr}`);
  let retries = 5;
  const tryDelete = () => {
    try {
      if (fs.existsSync(sessionPath)) {
        fs.rmSync(sessionPath, { recursive: true, force: true });
        console.log(`[WhatsApp-Web Service] Successfully deleted session directory for User ${userIdStr}`);
      }
    } catch (e) {
      if (retries > 0) {
        retries--;
        setTimeout(tryDelete, 1000);
      } else {
        console.log(`[WhatsApp-Web Service] Failed to delete session directory after retries: ${e.message}`);
      }
    }
  };
  setTimeout(tryDelete, 1000);

  return res.json({ status: 'success', message: 'WhatsApp session logged out successfully.' });
});

process.on('uncaughtException', (err) => {
  console.error('[WhatsApp-Web UncaughtException]:', err.message || err);
});

process.on('unhandledRejection', (err) => {
  console.error('[WhatsApp-Web UnhandledRejection]:', err.message || err);
});

app.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`NexusAI Baileys WhatsApp Service running on port ${PORT}`);
  console.log(`Targeting FastAPI Backend: ${FASTAPI_URL}`);
  console.log(`====================================================`);

  (async () => {
    try {
      const sessionDirs = fs.readdirSync(SESSIONS_DIR);
      for (const dir of sessionDirs) {
        if (dir.startsWith('session-')) {
          const userId = dir.replace('session-', '');
          console.log(`[WhatsApp-Web Service] Auto-restoring session for User ${userId}...`);
          initWhatsAppSession(userId).catch(e => console.error(e));
          
          await new Promise(r => setTimeout(r, 2000));
        }
      }
    } catch (err) {
      console.error(`[WhatsApp-Web Service] Error auto-loading sessions:`, err);
    }
  })();
});
