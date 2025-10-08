const http = require('http');
const OpenAI = require('openai');
const openai = process.env.OPENAI_API_KEY ? new OpenAI({ apiKey: process.env.OPENAI_API_KEY }) : null;

const PORT = Number(process.env.PORT || process.env.CHAT_PORT || 3000);
const allowedOrigin = process.env.ALLOWED_ORIGIN || '*';
const MCP_URL = process.env.MCP_URL || 'http://localhost:8787/mcp';

async function callMcp(tool, input, req) {
  const headers = { 'content-type': 'application/json' };
  const userJwt = req.headers['x-user-jwt'] || req.headers['X-User-Jwt'];
  if (userJwt) headers['x-user-jwt'] = String(userJwt);
  const resp = await fetch(MCP_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify({ tool, input }),
  });
  const data = await resp.json();
  if (!resp.ok || !data.ok) {
    const err = new Error((data && data.error) || `MCP error ${resp.status}`);
    err.statusCode = resp.status;
    throw err;
  }
  return data.result;
}

function inferIntent(message) {
  const m = String(message || '').toLowerCase();
  if (/(trade|position|ouvrir|fermer|achat|vente)/.test(m)) return { tool: 'trades.list', input: { open_only: true } };
  if (/(banque|classe|allocation|actifs)/.test(m)) return { tool: 'banking.summary', input: {} };
  if (/(immobilier|appartement|rendement|loyer|lausanne|genève)/.test(m)) return { tool: 'realestate.listings.search', input: { location: message } };
  if (/(marché|analyse|risque|opportunités)/.test(m)) return { tool: 'market.analyses.search', input: { page: 1, page_size: 10 } };
  return { tool: 'items.search', input: { q: message, page: 1, page_size: 10 } };
}

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

      // Intelligent fallback: call MCP + summarize with OpenAI if key provided
      if (openai) {
        const intent = inferIntent(message);
        let toolResult = null;
        try {
          toolResult = await callMcp(intent.tool, intent.input, req);
        } catch (e) {
          toolResult = { error: String(e && e.message) };
        }

        const prompt = [
          { role: 'system', content: "Assistant portefeuille. Réponds en français, concis. Utilise STRICTEMENT les données JSON fournies (résultats MCP). N'invente pas de chiffres." },
          { role: 'user', content: `Question:\n${message}\n\nRésultats MCP (${intent.tool}):\n${JSON.stringify(toolResult).slice(0, 15000)}` },
        ];
        const completion = await openai.chat.completions.create({ model: 'gpt-4o-mini', temperature: 0.3, messages: prompt });
        const text = completion?.choices?.[0]?.message?.content || 'Je n\'ai pas pu générer de réponse.';

        res.writeHead(200, {
          'Access-Control-Allow-Origin': allowedOrigin,
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
          'x-agent-mode': 'openai+mcp',
        });
        res.write(`data: ${JSON.stringify({ type: 'text', text })}\n\n`);
      res.end();
      return;
    }

      // Pure fallback SSE (no OpenAI key)
      res.writeHead(200, {
        'Access-Control-Allow-Origin': allowedOrigin,
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
        'x-agent-mode': 'fallback',
      });
      const response = { type: 'text', text: `Fallback: reçu "${message}". Ajoute OPENAI_API_KEY pour activer le mode intelligent (MCP).` };
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

