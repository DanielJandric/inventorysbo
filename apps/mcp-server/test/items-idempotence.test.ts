import { describe, it, expect } from 'vitest';
import app from '../src/index.js';

describe('items.set_prices idempotence (dry run path only in tests)', () => {
  it('defaults to dry_run true and returns preview', async () => {
    const res = await app.inject({ method: 'POST', url: '/mcp', payload: { tool: 'items.set_prices', input: { id: 1, prices: { sold_price: 100 }, effective_date: '2025-10-07' } } });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.ok).toBe(true);
    expect(body.result.preview).toBeTruthy();
  });
});


