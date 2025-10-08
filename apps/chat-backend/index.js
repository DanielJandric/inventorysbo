const http = require('http');

let agentsAvailable = false;
let createAgent;
let hostedMcpTool;
try {
  ({ createAgent, hostedMcpTool } = require('@openai/agents'));
  agentsAvailable = true;
} catch (e) {
  // Agents SDK not available; will use fallback
}

const PORT = Number(process.env.PORT || process.env.CHAT_PORT || 3000);
const allowedOrigin = process.env.ALLOWED_ORIGIN || '*';
const MCP_URL = process.env.MCP_URL || 'http://localhost:8787/mcp';

function handleOptions(req, res) {
  res.writeHead(204, {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-user-jwt',
  });
  res.end();
}

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-cache',
  });
  res.end(JSON.stringify(data));
}

function parseJsonBody(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', (chunk) => {
      raw += chunk;
      if (raw.length > 2 * 1024 * 1024) {
        reject(new Error('Payload too large'));
        req.destroy();
      }
    });
    req.on('end', () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

const server = http.createServer(async (req, res) => {
  const { method, url } = req;

  if (method === 'OPTIONS') return handleOptions(req, res);

  if (method === 'GET' && url === '/health') {
    return sendJson(res, 200, { ok: true });
  }

  if (method === 'POST' && url === '/chat') {
    try {
      const body = await parseJsonBody(req);
      const message = (body && (body.message || body.input)) || '';
      if (!message) return sendJson(res, 400, { error: 'Missing input' });

      const keyPresent = Boolean(process.env.OPENAI_API_KEY);
      const canUseAgents = agentsAvailable && keyPresent;

      if (canUseAgents) {
        // Lazy agent init with hosted MCP tool
        if (!server._agent) {
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
          server._agent = createAgent({
            model: 'gpt-4.1-mini',
            system: "Assistant portefeuille. N'invente pas de chiffres: utilise les outils MCP.",
            tools: [tool],
          });
        }

        res.writeHead(200, {
          'Access-Control-Allow-Origin': allowedOrigin,
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
          'x-agent-mode': 'agents',
        });

        const stream = await server._agent.respond({ input: message, stream: true, request: req });
        for await (const chunk of stream) {
          res.write(`data: ${typeof chunk === 'string' ? chunk : JSON.stringify(chunk)}\n\n`);
        }
        res.end();
        return;
      }

      // Fallback SSE mode
      res.writeHead(200, {
        'Access-Control-Allow-Origin': allowedOrigin,
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
        'x-agent-mode': 'fallback',
      });
      const response = { type: 'text', text: `Fallback mode: Received message "${message}". Agents SDK not available or OPENAI_API_KEY missing.` };
      res.write(`data: ${JSON.stringify(response)}\n\n`);
      res.end();
      return;
    } catch (e) {
      return sendJson(res, 500, { error: 'Internal server error' });
    }
  }

  sendJson(res, 404, { error: 'Not Found' });
});

server.listen(PORT, () => {
  console.log(`chat-backend listening on :${PORT}`);
});

module.exports = server;

