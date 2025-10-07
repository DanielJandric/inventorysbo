import { describe, it, expect } from 'vitest';
import app from '../src/index.js';

describe('trades tools', () => {
  it('enforces option_type when is_option=true', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/mcp',
      payload: {
        tool: 'trades.record',
        input: {
          symbol: 'AAPL',
          direction: 'call',
          entry_date: new Date().toISOString(),
          entry_price: 1,
          is_option: true
        },
      },
    });
    expect(res.statusCode).toBeGreaterThanOrEqual(400);
  });
});


