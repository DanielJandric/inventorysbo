require('dotenv').config();
const http = require('http');

const PORT = Number(process.env.PORT || 8787);

function sendJson(res, statusCode, data, extraHeaders) {
  const headers = Object.assign(
    {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-cache',
    },
    extraHeaders || {}
  );
  res.writeHead(statusCode, headers);
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

  if (method === 'GET' && url === '/health') {
    return sendJson(res, 200, { ok: true });
  }

  if (method === 'POST' && url === '/mcp') {
    const start = Date.now();
    try {
      const body = await parseJsonBody(req);
      if (!body || typeof body !== 'object') {
        return sendJson(res, 400, { ok: false, error: 'Invalid JSON body' });
      }

      const toolName = body.tool || body.name;
      const args = body.input || body.arguments || body.params;

      if (!toolName || typeof toolName !== 'string') {
        return sendJson(res, 400, { ok: false, error: 'Missing tool name' });
      }

      const latency = Date.now() - start;
      return sendJson(
        res,
        200,
        {
          ok: true,
          tool: toolName,
          result: { message: `Tool ${toolName} called with args: ${JSON.stringify(args)}` },
        },
        { 'x-latency-ms': String(latency) }
      );
    } catch (err) {
      return sendJson(res, 400, { ok: false, error: 'Bad Request', details: String(err && err.message) });
    }
  }

  sendJson(res, 404, { ok: false, error: 'Not Found' });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`MCP server listening on :${PORT}`);
});

module.exports = server;

