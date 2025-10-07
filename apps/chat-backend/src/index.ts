import 'dotenv/config';
import express from 'express';
import { createAgent, hostedMcpTool } from '@openai/agents';

const app = express();
app.use(express.json());

// Basic CORS without external dependency
const allowedOrigin = process.env.ALLOWED_ORIGIN || '*';
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', allowedOrigin);
  res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-user-jwt');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

const forwardJwtToMcp: express.RequestHandler = (req, _res, next) => {
  const auth = req.headers.authorization;
  const bearer = auth?.startsWith('Bearer ') ? auth.slice(7) : undefined;
  if (bearer) req.headers['x-user-jwt'] = bearer;
  next();
};

const inventoryTool = hostedMcpTool({
  label: 'inventory-supabase',
  url: process.env.MCP_URL || 'http://localhost:8787/mcp',
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
  extra_headers: (req) => ({ 'x-user-jwt': (req.headers['x-user-jwt'] as string) ?? '' }),
});

const agent = createAgent({
  model: 'gpt-4.1-mini',
  system: "Assistant portefeuille. N'invente pas de chiffres: utilise les outils MCP.",
  tools: [inventoryTool],
});

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.post('/chat', forwardJwtToMcp, async (req, res) => {
  const { message } = req.body as { message: string };
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');
  const stream = await agent.respond({ input: message, stream: true, request: req });
  for await (const chunk of stream) {
    res.write(`data: ${typeof chunk === 'string' ? chunk : JSON.stringify(chunk)}\n\n`);
  }
  res.end();
});

const PORT = Number(process.env.PORT || process.env.CHAT_PORT || 3000);
app.listen(PORT, () => console.log(`chat-backend listening on :${PORT}`));


