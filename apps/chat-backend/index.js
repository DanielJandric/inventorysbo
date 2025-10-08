const http = require('http');
const OpenAI = require('openai');
const openai = process.env.OPENAI_API_KEY ? new OpenAI({ apiKey: process.env.OPENAI_API_KEY }) : null;
const allowedTools = [
      'items.search', 'items.get', 'items.similar',
      'items.update_status', 'items.set_prices',
      'banking.classes.list', 'banking.summary',
      'market.analyses.search', 'market.analyses.get', 'market.analyses.upsert',
      'realestate.listings.search',
      'trades.list', 'trades.record', 'trades.close',
      'exports.generate'
];

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

function detectCountQuery(message) {
  const m = String(message || '').toLowerCase();
  const isHowMany = /(combien|how many)/.test(m);
  if (!isHowMany) return null;
  if (/voitures?/.test(m)) {
    const fourSeats = /(4\s*(places|p))/i.test(message);
    const q = fourSeats ? '4 places' : undefined;
    return { category: 'Voitures', q };
  }
  if (/bateaux?/.test(m) || /(yacht|sunseeker|axopar)/.test(m)) {
    return { category: 'Bateaux' };
  }
  return null;
}

function getToolDefs() {
  return [
    {
      type: 'function',
      function: {
        name: 'call_mcp',
        description: 'Call an MCP tool exposed by the inventory MCP server',
        parameters: {
          type: 'object',
          properties: {
            tool: { type: 'string', enum: allowedTools },
            input: { type: 'object', additionalProperties: true },
          },
          required: ['tool', 'input'],
          additionalProperties: false,
        },
      },
    },
  ];
}

async function runWithTools(message, req) {
  const sys = {
    role: 'system',
    content: "Assistant portefeuille BONVIN. Réponds en français, concis et fiable. Utilise les outils MCP via la fonction call_mcp quand nécessaire. N'invente pas de chiffres: privilégie les données MCP.",
  };
  const user = { role: 'user', content: String(message) };

  // First pass: allow tool selection
  const first = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    temperature: 0.2,
    messages: [sys, user],
    tools: getToolDefs(),
    tool_choice: 'auto',
  });

  const msg = first.choices?.[0]?.message;
  const toolCalls = msg?.tool_calls || [];
  if (!toolCalls.length) {
    return msg?.content || "Je n'ai pas de réponse.";
  }

  const convo = [sys, user, msg];
  for (const call of toolCalls) {
    if (call.type !== 'function' || !call.function) continue;
    const fn = call.function.name;
    let args = {};
    try { args = JSON.parse(call.function.arguments || '{}'); } catch {}
    if (fn !== 'call_mcp' || !args.tool) continue;
    if (!allowedTools.includes(args.tool)) {
      convo.push({ role: 'tool', tool_call_id: call.id, content: JSON.stringify({ error: 'Tool not allowed' }) });
      continue;
    }
    let result;
    try {
      result = await callMcp(args.tool, args.input || {}, req);
    } catch (e) {
      result = { error: String(e && e.message) };
    }
    convo.push({ role: 'tool', tool_call_id: call.id, content: JSON.stringify(result).slice(0, 20000) });
  }

  const second = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    temperature: 0.2,
    messages: convo,
  });
  return second.choices?.[0]?.message?.content || 'Pas de réponse.';
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

      // Handle explicit counting queries deterministically (no hallucinations)
      const countIntent = detectCountQuery(message);
      if (countIntent) {
        const input = { page: 1, page_size: 1, filters: { category: countIntent.category } };
        if (countIntent.q) input.q = countIntent.q;
        let result;
        try {
          result = await callMcp('items.search', input, req);
        } catch (e) {
          result = null;
        }
        const total = (result && typeof result.total === 'number') ? result.total : 0;
        const label = countIntent.category.toLowerCase();
        const suffix = countIntent.q ? ` (${countIntent.q})` : '';
        const text = `Vous avez ${total} ${label}${suffix ? suffix : ''}.`;
        res.writeHead(200, {
          'Access-Control-Allow-Origin': allowedOrigin,
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
          'x-agent-mode': 'deterministic',
        });
        res.write(`data: ${JSON.stringify({ type: 'text', text })}\n\n`);
        res.end();
        return;
      }

      // Intelligent fallback: tool-augmented with OpenAI function calling if key provided
      if (openai) {
        const text = await runWithTools(message, req);

        res.writeHead(200, {
          'Access-Control-Allow-Origin': allowedOrigin,
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
          'x-agent-mode': 'openai+tools+mcp',
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

