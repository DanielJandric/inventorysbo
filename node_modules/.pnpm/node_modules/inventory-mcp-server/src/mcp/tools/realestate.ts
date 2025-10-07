import { z } from 'zod';
import { dateSchema, moneySchema } from '../../lib/validation.js';
import type { Registry } from '../index.js';

export function realestateTools(tool: <I extends z.ZodTypeAny, O>(def: { input: I; handler: any }) => any): Registry {
  return {
    'realestate.listings.search': tool({
      input: z
        .object({
          status: z.string().optional(),
          source_site: z.string().optional(),
          location: z.string().optional(),
          price_max: moneySchema.optional(),
          yield_min: z.number().min(0).optional(),
          scraped_after: dateSchema.optional(),
        })
        .strict(),
      async handler(ctx, input) {
        let q = ctx.supabase.from('real_estate_listings').select('*').order('updated_at', { ascending: false }).limit(200);
        if (input.status) q = q.eq('status', input.status);
        if (input.source_site) q = q.eq('source_site', input.source_site);
        if (input.location) q = q.ilike('location', `%${input.location}%`);
        if (typeof input.price_max === 'number') q = q.lte('price', input.price_max);
        if (typeof input.yield_min === 'number') q = q.gte('yield_percentage', input.yield_min);
        if (input.scraped_after) q = q.gte('scraped_at', input.scraped_after);
        const resp = await q;
        if (resp.error) throw resp.error;
        return { items: resp.data || [] };
      },
    }),
  };
}


