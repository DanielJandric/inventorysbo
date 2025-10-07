import { describe, it, expect } from 'vitest';
import app from '../src/index.js';

describe('market tools', () => {
  it('upsert dry-run works', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/mcp',
      payload: {
        tool: 'market.analyses.upsert',
        input: { analysis_type: 'daily', summary: 'Résumé', dry_run: true },
      },
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.ok).toBe(true);
    expect(body.result.preview).toBeTruthy();
  });
});


