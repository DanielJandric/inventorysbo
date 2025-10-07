const fastify = require('fastify');
const rateLimit = require('@fastify/rate-limit');
const sensible = require('@fastify/sensible');
require('dotenv').config();

const LOG_LEVEL = process.env.LOG_LEVEL || 'info';
const PORT = Number(process.env.PORT || 8787);

const app = fastify({
  logger: { level: LOG_LEVEL },
  requestTimeout: 25000,
});

// Register plugins
app.register(sensible);
app.register(rateLimit, {
  max: 60,
  timeWindow: '1 minute',
});

// Health check
app.get('/health', async () => ({ ok: true }));

// MCP endpoint - simplified version
app.post('/mcp', async (request, reply) => {
  const start = Date.now();
  const body = request.body;

  if (!body || typeof body !== 'object') {
    reply.code(400);
    return { ok: false, error: 'Invalid JSON body' };
  }

  const toolName = body.tool || body.name;
  const args = body.input || body.arguments || body.params;

  if (!toolName || typeof toolName !== 'string') {
    reply.code(400);
    return { ok: false, error: 'Missing tool name' };
  }

  // Simple response for now
  const latency = Date.now() - start;
  reply.header('x-latency-ms', String(latency));
  
  return { 
    ok: true, 
    tool: toolName, 
    result: { message: `Tool ${toolName} called with args: ${JSON.stringify(args)}` }
  };
});

// Start server
app.listen({ port: PORT, host: '0.0.0.0' })
  .then(() => {
    app.log.info({ port: PORT }, 'MCP server listening');
  })
  .catch((err) => {
    app.log.error(err, 'Failed to start server');
    process.exit(1);
  });

module.exports = app;

