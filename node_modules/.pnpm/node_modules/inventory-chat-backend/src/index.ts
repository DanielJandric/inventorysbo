import express, { Request, Response, NextFunction } from 'express';

let createAgent: any;
let hostedMcpTool: any;
let agentsAvailable = false;

async function loadAgents() {
  try {
    const mod = await import('@openai/agents');
    createAgent = (mod as any).createAgent;
    hostedMcpTool = (mod as any).hostedMcpTool;
    agentsAvailable = true;
  } catch (e) {
    console.warn('Agents SDK not available; falling back to stub.');
    createAgent = (cfg: any) => ({ respond: async ({ input }: any) => `Agents SDK indisponible. Message: ${input}` });
    hostedMcpTool = (_cfg: any) => ({ label: 'stub', url: '', allowed_tools: [] });
  }
}

const app = express();
app.use(express.json());

// Basic CORS without external dependency
const allowedOrigin = process.env.ALLOWED_ORIGIN || '*';
app.use((req: Request, res: Response, next: NextFunction) => {
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

let agent: any;

app.get('/health', (_req: Request, res: Response) => {
  res.json({ ok: true });
});

app.post('/chat', forwardJwtToMcp, async (req: Request, res: Response) => {
  if (!createAgent) {
    await loadAgents();
    if (!agent) {
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
        extra_headers: (req: Request) => ({ 'x-user-jwt': (req.headers['x-user-jwt'] as string) ?? '' }),
      });
      agent = createAgent({
        model: 'gpt-4.1-mini',
        system: "Assistant portefeuille. N'invente pas de chiffres: utilise les outils MCP.",
        tools: [inventoryTool],
      });
    }
  }

  const { message } = req.body as { message: string };
  res.setHeader('x-agent-mode', agentsAvailable ? 'agents' : 'fallback');
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');
  const stream = await agent.respond({ input: message, stream: true, request: req });
  for await (const chunk of stream as AsyncIterable<any>) {
    res.write(`data: ${typeof chunk === 'string' ? chunk : JSON.stringify(chunk)}\n\n`);
  }
  res.end();
});

const PORT = Number(process.env.PORT || process.env.CHAT_PORT || 3000);
app.listen(PORT, () => console.log(`chat-backend listening on :${PORT}`));


