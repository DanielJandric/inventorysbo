const express = require('express');
require('dotenv').config();

let agentsAvailable = false;
let createAgent;
let hostedMcpTool;
try {
  ({ createAgent, hostedMcpTool } = require('@openai/agents'));
  agentsAvailable = true;
} catch (e) {
  console.warn('Agents SDK not available; using fallback.');
}

const app = express();
app.use(express.json());

const PORT = Number(process.env.PORT || process.env.CHAT_PORT || 3000);
const allowedOrigin = process.env.ALLOWED_ORIGIN || '*';
const MCP_URL = process.env.MCP_URL || 'http://localhost:8787/mcp';

// CORS middleware
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', allowedOrigin);
  res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-user-jwt');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// Health check
app.get('/health', (req, res) => {
  res.json({ ok: true });
});

let agent = null;
async function ensureAgentLoaded(req) {
  if (!agentsAvailable) return null;
  if (agent) return agent;

  const tool = hostedMcpTool({
    label: 'inventory-supabase',
    url: MCP_URL,
    allowed_tools: [
      'items.search', 'items.get', 'items.similar',
      'items.update_status', 'items.set_prices',
      'banking.classes.list', 'banking.summary',
      'market.analyses.search', 'market.analyses.get', 'market.analyses.upsert',
      'realestate.listings.search',
      'trades.list', 'trades.record', 'trades.close',
      'exports.generate'
    ],
    timeout_ms: 120000,
    extra_headers: (_req) => ({ 'x-user-jwt': _req.headers['x-user-jwt'] || '' }),
  });

  agent = createAgent({
    model: 'gpt-4.1-mini',
    system: "Assistant portefeuille. N'invente pas de chiffres: utilise les outils MCP.",
    tools: [tool],
  });
  return agent;
}

// Chat endpoint with agents integration + fallback
app.post('/chat', async (req, res) => {
  try {
    const message = (req.body && (req.body.message || req.body.input)) || '';
    if (!message) {
      return res.status(400).json({ error: 'Missing input' });
    }

    const keyPresent = Boolean(process.env.OPENAI_API_KEY);
    const canUseAgents = agentsAvailable && keyPresent;

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    if (canUseAgents) {
      res.setHeader('x-agent-mode', 'agents');
      const agentInstance = await ensureAgentLoaded(req);
      if (!agentInstance) throw new Error('Agent init failed');

      const stream = await agentInstance.respond({ input: message, stream: true, request: req });
      for await (const chunk of stream) {
        res.write(`data: ${typeof chunk === 'string' ? chunk : JSON.stringify(chunk)}\n\n`);
      }
      res.end();
      return;
    }

    // Fallback mode
    res.setHeader('x-agent-mode', 'fallback');
    const response = {
      type: 'text',
      text: `Fallback mode: Received message "${message}". Agent SDK not available or OPENAI_API_KEY missing.`,
    };
    res.write(`data: ${JSON.stringify(response)}\n\n`);
    res.end();
  } catch (error) {
    console.error('Chat error:', error);
    try {
      res.write(`data: ${JSON.stringify({ type: 'error', error: 'Internal server error' })}\n\n`);
      res.end();
    } catch (_) {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`chat-backend listening on :${PORT}`);
});

module.exports = app;

