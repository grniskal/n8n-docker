// Userbot HTTP API using GramJS
// Deploy to Railway: heroic-creativity

import express from "express";
import { TelegramClient } from "telegram";
import { StringSession } from "telegram/sessions/index.js";

const app = express();
app.use(express.json());

const API_ID = parseInt(process.env.TELEGRAM_API_ID || "34612084");
const API_HASH = process.env.TELEGRAM_API_HASH || "0c9fe2b6a7180190014287de5699aaf0";
const SESSION_STRING = process.env.TELEGRAM_SESSION || "";
const PORT = process.env.PORT || 8080;

let client;
let isReady = false;

// Initialize Telegram client
async function initClient() {
  try {
    console.log("Initializing Telegram client...");
    const session = new StringSession(SESSION_STRING);
    client = new TelegramClient(session, API_ID, API_HASH, {
      connectionRetries: 5,
    });

    await client.connect();

    if (!SESSION_STRING) {
      console.warn("WARNING: No session string provided. Client will not work.");
      isReady = false;
    } else {
      console.log("Connected to Telegram!");
      const me = await client.getMe();
      console.log(`Logged in as: ${me.username || me.firstName} (${me.id})`);
      isReady = true;
    }
  } catch (error) {
    console.error("Failed to initialize client:", error.message);
    isReady = false;
  }
}

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({
    status: isReady ? "ready" : "not_ready",
    session: SESSION_STRING ? "provided" : "missing",
    timestamp: new Date().toISOString(),
  });
});

// Send message endpoint
app.post("/sendMessage", async (req, res) => {
  if (!isReady) {
    return res.status(503).json({
      error: "Client not ready",
      message: "Session string not configured or client failed to connect",
    });
  }

  const { chatId, text, channelId } = req.body;

  if (!chatId || !text) {
    return res.status(400).json({
      error: "Missing required fields",
      required: ["chatId", "text"],
    });
  }

  try {
    let targetEntity;

    // Step 1: Resolve the user entity
    // Username (@xxx) works directly via contacts.resolveUsername
    // Numeric ID needs the entity to be cached first
    const target = chatId.toString();

    if (target.startsWith('@')) {
      // Resolve username - this calls contacts.resolveUsername internally
      console.log(`Resolving username: ${target}`);
      targetEntity = await client.getEntity(target);
      console.log(`Resolved to user ID: ${targetEntity.id}`);
    } else if (channelId && !isNaN(channelId)) {
      // If we have a numeric Telegram channel ID, get user from channel
      try {
        console.log(`Getting user ${target} from Telegram channel ${channelId}`);
        const channel = await client.getEntity(parseInt(channelId));
        const participant = await client.getParticipants(channel, { limit: 1, search: target });
        if (participant && participant.length > 0) {
          targetEntity = participant[0];
          console.log(`Found user in channel: ${targetEntity.id}`);
        }
      } catch (e) {
        console.warn("Channel lookup failed:", e.message);
      }
    }

    // Fallback: try direct (works if entity was previously cached)
    if (!targetEntity) {
      targetEntity = target;
    }

    // Step 2: Send message
    const result = await client.sendMessage(targetEntity, { message: text });

    res.json({
      success: true,
      messageId: result.id,
      date: result.date,
      chatId: chatId,
    });
  } catch (error) {
    console.error("Send message error:", error);
    res.status(500).json({
      error: "Failed to send message",
      message: error.message,
    });
  }
});

// Get user info
app.get("/me", async (req, res) => {
  if (!isReady) {
    return res.status(503).json({ error: "Client not ready" });
  }

  try {
    const me = await client.getMe();
    res.json({
      id: me.id.toString(),
      username: me.username,
      firstName: me.firstName,
      lastName: me.lastName,
      phone: me.phone,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(PORT, async () => {
  console.log(`Userbot API listening on port ${PORT}`);
  await initClient();
});
