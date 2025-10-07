import fastify, { FastifyInstance } from 'fastify';
import rateLimit from '@fastify/rate-limit';
import sensible from '@fastify/sensible';
import dotenv from 'dotenv';
import { createAuditLogger, withAudit } from './lib/audit.js';
import { createSupabaseClient } from './lib/supabase.js';
import { registry } from './mcp/index.js';

dotenv.config();

const LOG_LEVEL = process.env.LOG_LEVEL || 'info';
const PORT = Number(process.env.PORT || 8787);

const app: FastifyInstance = fastify({
  logger: { level: LOG_LEVEL },
  requestTimeout: 25000,
});

await app.register(sensible);
await app.register(rateLimit, {
  max: 60,
  timeWindow: '1 minute',
});

const audit = createAuditLogger(app.log);

app.get('/health', async () => ({ ok: true }));

app.post('/mcp', async (request, reply) => {
  const start = Date.now();
  const body = request.body as Record<string, unknown> | undefined;

  if (!body || typeof body !== 'object') {
    reply.code(400);
    return { ok: false, error: 'Invalid JSON body' };
  }

  const toolName = (body['tool'] || body['name']) as string | undefined;
  const args = (body['input'] || body['arguments'] || body['params']) as unknown;

  if (!toolName || typeof toolName !== 'string') {
    reply.code(400);
    return { ok: false, error: 'Missing tool name' };
  }

  const tool = registry[toolName];
  if (!tool) {
    reply.code(404);
    return { ok: false, error: `Unknown tool: ${toolName}` };
  }

  // Validate input early to allow running tests without Supabase env
  let validated: any;
  try {
    validated = tool.input.parse(args);
  } catch (e: any) {
    reply.code(400);
    return { ok: false, error: e.message };
  }

  const supabase = createSupabaseClient(request.headers);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 25000);

  try {
    const result = await withAudit(audit, toolName, validated, async () => {
      // Each handler receives ctx with supabase and headers for extra context
      return await tool.handler({ supabase, headers: request.headers, signal: controller.signal }, validated);
    });

    reply.code(200);
    return { ok: true, tool: toolName, result };
  } catch (err: any) {
    const msg = err?.message || 'Unhandled error';
    const status = err?.statusCode || 500;
    app.log.error({ err }, 'MCP tool error');
    reply.code(status);
    return { ok: false, error: msg, details: err?.details };
  } finally {
    clearTimeout(timeout);
    const latency = Date.now() - start;
    reply.header('x-latency-ms', String(latency));
  }
});

if (import.meta.url === `file://${process.argv[1]}`) {
  app.listen({ port: PORT, host: '0.0.0.0' })
    .then(() => {
      app.log.info({ port: PORT }, 'MCP server listening');
    })
    .catch((err) => {
      app.log.error(err, 'Failed to start server');
      process.exit(1);
    });
}

export default app;


