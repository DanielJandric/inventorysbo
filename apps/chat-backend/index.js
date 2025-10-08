const http = require('http');
const OpenAI = require('openai');
const openai = process.env.OPENAI_API_KEY ? new OpenAI({ apiKey: process.env.OPENAI_API_KEY }) : null;
const MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';
const MAX_OUTPUT_TOKENS = Number(process.env.OPENAI_MAX_OUTPUT_TOKENS || 2048);
const REASONING_EFFORT = process.env.OPENAI_REASONING_EFFORT || 'high';
const allowedTools = [
      'items.search', 'items.get', 'items.similar',
      'items.update_status', 'items.set_prices',
  'items.summary',
      'banking.classes.list', 'banking.summary',
      'market.analyses.search', 'market.analyses.get', 'market.analyses.upsert',
      'realestate.listings.search',
      'trades.list', 'trades.record', 'trades.close',
      'exports.generate'
];

const PORT = Number(process.env.PORT || process.env.CHAT_PORT || 3000);
const allowedOrigin = process.env.ALLOWED_ORIGIN || '*';
const MCP_URL = process.env.MCP_URL || 'http://localhost:8787/mcp';

const sessions = new Map(); // sessionId -> [{role, content}]

function getSessionId(req, body) {
  return (
    (body && (body.session_id || body.sessionId)) ||
    req.headers['x-session-id'] ||
    `${req.socket.remoteAddress || 'anon'}:${req.headers['user-agent'] || ''}`
  );
}

function pushHistory(sessionId, role, content) {
  if (!sessionId) return;
  const arr = sessions.get(sessionId) || [];
  arr.push({ role, content: String(content).slice(0, 4000) });
  while (arr.length > 12) arr.shift();
  sessions.set(sessionId, arr);
}

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
    return { category: 'Voitures', fourSeats };
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

function mkInput(systemText, history, userText) {
  const arr = [];
  if (systemText) arr.push({ role: 'system', content: [{ type: 'text', text: String(systemText) }] });
  for (const h of history || []) {
    if (!h || !h.role) continue;
    arr.push({ role: h.role, content: [{ type: 'text', text: String(h.content || '') }] });
  }
  if (userText) arr.push({ role: 'user', content: [{ type: 'text', text: String(userText) }] });
  return arr;
}

function extractOutputText(resp) {
  try {
    if (resp && typeof resp.output_text === 'string' && resp.output_text) return resp.output_text;
    const out = resp && resp.output;
    if (Array.isArray(out)) {
      let txt = '';
      for (const o of out) {
        const c = o && o.content;
        if (Array.isArray(c)) {
          for (const p of c) {
            if (p && (p.type === 'output_text' || p.type === 'text') && typeof p.text === 'string') txt += p.text;
          }
        }
      }
      if (txt) return txt;
    }
  } catch {}
  return '';
}

async function runWithTools(message, req) {
  const sessionId = getSessionId(req, { message });
  const history = sessions.get(sessionId) || [];
  const sys = {
    role: 'system',
    content:
      "Assistant portefeuille BONVIN. Réponds en français, concis et fiable. Utilise les outils MCP via la fonction call_mcp quand nécessaire. N'invente pas de chiffres: privilégie les données MCP.",
  };
  const user = { role: 'user', content: String(message) };

  // Build input for Responses API
  const input = mkInput(sys.content, history.slice(-6), user.content);
  let resp = await openai.responses.create({
    model: MODEL,
    input,
    tools: getToolDefs(),
    temperature: 0.2,
    max_output_tokens: MAX_OUTPUT_TOKENS,
    reasoning: { effort: REASONING_EFFORT },
  });

  // Handle tool calls iteratively
  for (let step = 0; step < 4; step++) {
    const required = resp && resp.required_action;
    const calls = required && required.type === 'submit_tool_outputs' ? (required.submit_tool_outputs?.tool_calls || []) : [];
    if (!calls.length) break;

    const tool_outputs = [];
    for (const c of calls) {
      const name = c.name;
      if (name !== 'call_mcp') {
        tool_outputs.push({ tool_call_id: c.id, output: JSON.stringify({ error: 'Unknown tool' }) });
        continue;
      }
      let args = {};
      try { args = JSON.parse(c.arguments || '{}'); } catch {}
      if (!args.tool || !allowedTools.includes(args.tool)) {
        tool_outputs.push({ tool_call_id: c.id, output: JSON.stringify({ error: 'Tool not allowed' }) });
        continue;
      }
      let result;
      try {
        result = await callMcp(args.tool, args.input || {}, req);
      } catch (e) {
        result = { error: String(e && e.message) };
      }
      tool_outputs.push({ tool_call_id: c.id, output: JSON.stringify(result).slice(0, 20000) });
    }
    resp = await openai.responses.submitToolOutputs(resp.id, { tool_outputs });
  }

  const text = extractOutputText(resp) || 'Pas de réponse.';
  pushHistory(sessionId, 'user', message);
  pushHistory(sessionId, 'assistant', text);
  return text;
}

function detectFastestCarQuery(message) {
  const m = String(message || '').toLowerCase();
  const triggers = ['plus rapide', 'vitesse', '0-100', '0 à 100', '0 a 100'];
  const hasCar = /voitures?/.test(m) || /auto|car|supercar/.test(m);
  return hasCar && triggers.some(t => m.includes(t));
}

function parseNumber(v) {
  if (v == null) return null;
  const n = Number(String(v).replace(/[^0-9.\-]/g, ''));
  return Number.isFinite(n) ? n : null;
}

function pickTopSpeed(it) {
  const keys = ['top_speed', 'speed_max', 'vitesse_max', 'max_speed'];
  for (const k of keys) {
    if (it[k] != null) return parseNumber(it[k]);
  }
  return null;
}

function pickZeroToHundred(it) {
  const keys = ['zero_to_hundred', 'zero_to_sixty', 'zero_100', 'zero100', 'acceleration_0_100'];
  for (const k of keys) {
    if (it[k] != null) return parseNumber(it[k]);
  }
  return null;
}

function pickHorsepower(it) {
  const keys = ['horsepower', 'hp', 'power_hp', 'puissance_ch'];
  for (const k of keys) {
    if (it[k] != null) return parseNumber(it[k]);
  }
  return null;
}

async function answerFastestCar(req, res, allowedOrigin) {
  let result = null;
  try {
    result = await callMcp('items.search', { page: 1, page_size: 200, filters: { category: 'Voitures', exclude_sold: true } }, req);
  } catch {}
  const items = (result && result.items) || [];
  if (!items.length) {
    const text = "Je n'ai pas trouvé de voitures actives dans votre collection.";
    res.writeHead(200, { 'Access-Control-Allow-Origin': allowedOrigin, 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache', Connection: 'keep-alive', 'x-agent-mode': 'deterministic' });
    res.write(`data: ${JSON.stringify({ type: 'text', text })}\n\n`);
    res.end();
    return;
  }

  // Try rank using available numeric attributes
  const ranked = items.map(it => {
    const ts = pickTopSpeed(it);
    const z = pickZeroToHundred(it);
    const hp = pickHorsepower(it);
    // Composite: prioritize top speed; fallback to 0-100 (lower is better), then horsepower
    const score = (ts != null ? ts * 1000 : 0) + (z != null ? (500 - z) * 10 : 0) + (hp != null ? hp : 0);
    return { it, ts, z, hp, score };
  });
  const anyMetrics = ranked.some(r => r.ts != null || r.z != null || r.hp != null);
  if (anyMetrics) {
    ranked.sort((a, b) => b.score - a.score);
    const best = ranked[0];
    const label = best.it.name || `${best.it.brand || ''} ${best.it.model || ''}`.trim();
    const details = [];
    if (best.ts != null) details.push(`${best.ts} km/h`);
    if (best.z != null) details.push(`${best.z} s (0-100)`);
    if (best.hp != null) details.push(`${best.hp} ch`);
    const text = `La voiture la plus rapide est ${label}${details.length ? ` (${details.join(', ')})` : ''}.`;
    res.writeHead(200, { 'Access-Control-Allow-Origin': allowedOrigin, 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache', Connection: 'keep-alive', 'x-agent-mode': 'deterministic' });
    res.write(`data: ${JSON.stringify({ type: 'text', text })}\n\n`);
    res.end();
    return;
  }

  // Otherwise, ask OpenAI to pick based on brand/model knowledge
  const brief = items.map(it => ({ id: it.id, brand: it.brand, model: it.model, name: it.name })).slice(0, 200);
  let winner = null;
  let why = '';
  if (openai) {
    const comp = await openai.responses.create({
      model: MODEL,
      input: mkInput(
        "Choisis la voiture la plus rapide (top speed prioritaire; sinon 0-100 le plus bas; sinon puissance). Réponds JSON: {id:number, reason:string}.",
        [],
        JSON.stringify(brief)
      ),
      max_output_tokens: MAX_OUTPUT_TOKENS,
      reasoning: { effort: REASONING_EFFORT },
    });
    try {
      const txt = extractOutputText(comp) || '{}';
      const obj = JSON.parse(txt);
      winner = items.find(it => Number(it.id) === Number(obj.id));
      why = String(obj.reason || '').slice(0, 300);
    } catch {}
  }
  const label = winner ? (winner.name || `${winner.brand || ''} ${winner.model || ''}`.trim()) : 'indéterminée';
  const text = winner ? `La voiture la plus rapide est ${label}.${why ? ` Raison: ${why}` : ''}` : "Je n'ai pas pu déterminer la voiture la plus rapide.";
  res.writeHead(200, { 'Access-Control-Allow-Origin': allowedOrigin, 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache', Connection: 'keep-alive', 'x-agent-mode': 'openai-judgement' });
  res.write(`data: ${JSON.stringify({ type: 'text', text })}\n\n`);
  res.end();
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
        const input = { page: 1, page_size: 1, filters: { category: countIntent.category, exclude_sold: true } };
        let result;
        try {
          result = await callMcp('items.search', input, req);
        } catch (e) {
          result = null;
        }
        let total = (result && typeof result.total === 'number') ? result.total : 0;

        // If 4 places requested, refine with OpenAI brand/model heuristic
        if (countIntent.fourSeats && total > 0 && openai) {
          const pageSize = Math.min(Math.max(total, 1), 200);
          let full;
          try {
            full = await callMcp('items.search', { page: 1, page_size: pageSize, filters: { category: countIntent.category, exclude_sold: true } }, req);
          } catch { full = null; }
          const items = (full && full.items) || [];
          const brief = items.map(it => ({ id: it.id, brand: it.brand, model: it.model, name: it.name })).slice(0, 200);
          const judge = await openai.responses.create({
            model: MODEL,
            input: mkInput(
              "Tu es un classifieur: pour chaque voiture (brand, model, name), dis '4p' si c'est un modèle 4 places, sinon 'autre'. Réponds uniquement une liste JSON d'ids 4 places.",
              [],
              JSON.stringify(brief)
            ),
            max_output_tokens: MAX_OUTPUT_TOKENS,
            reasoning: { effort: REASONING_EFFORT },
          });
          try {
            const txt = extractOutputText(judge) || '[]';
            const ids = JSON.parse(txt).map(Number).filter(n => Number.isInteger(n));
            total = ids.length;
          } catch {}
        }
        const label = countIntent.category.toLowerCase();
        const suffix = countIntent.fourSeats ? ' (4 places)' : '';
        const text = `Vous avez ${total} ${label}${suffix}.`;
        res.writeHead(200, {
          'Access-Control-Allow-Origin': allowedOrigin,
          'Content-Type': 'text/event-stream; charset=utf-8',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
          'x-agent-mode': 'deterministic',
        });
        res.write(`data: ${JSON.stringify({ type: 'text', text })}\n\n`);
        res.end();
        return;
      }

      // Fastest car query shortcut
      if (detectFastestCarQuery(message)) {
        await answerFastestCar(req, res, allowedOrigin);
        return;
      }

      // Intelligent fallback: tool-augmented with OpenAI function calling if key provided
      if (openai) {
        const text = await runWithTools(message, req);

        res.writeHead(200, {
          'Access-Control-Allow-Origin': allowedOrigin,
          'Content-Type': 'text/event-stream; charset=utf-8',
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

