import { describe, it, expect, vi } from 'vitest';
import app from '../src/index.js';

describe('items tools', () => {
  it('validates bad payload', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/mcp',
      payload: { tool: 'items.search', input: { page: -1 } },
    });
    expect(res.statusCode).toBe(400);
  });
});


