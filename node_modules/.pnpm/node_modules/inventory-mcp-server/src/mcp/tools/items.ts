import { z } from 'zod';
import { buildRange, dateSchema, moneySchema, paginationSchema } from '../../lib/validation.js';
import type { Registry } from '../index.js';
import OpenAI from 'openai';

const sortEnum = z.enum([
  'created_at_desc',
  'current_value_desc',
  'last_action_desc',
  'construction_year_desc',
  'name_asc',
]);

export function itemsTools(tool: <I extends z.ZodTypeAny, O>(def: { input: I; handler: any }) => any): Registry {
  return {
    'items.search': tool({
      input: z
        .object({
          q: z.string().min(1).optional(),
          filters: z
            .object({
              category: z.string().optional(),
              status: z.string().optional(),
              for_sale: z.boolean().optional(),
              location: z.string().optional(),
              price_min: moneySchema.optional(),
              price_max: moneySchema.optional(),
              construction_year_min: z.number().int().optional(),
              construction_year_max: z.number().int().optional(),
            })
            .strict()
            .default({}),
          sort: sortEnum.default('created_at_desc'),
          ...paginationSchema.shape,
        })
        .strict(),
      async handler(ctx, input) {
        const { page, page_size } = input;
        const { from, to } = buildRange(page, page_size);
        let q = ctx.supabase.from('items').select('*', { count: 'exact' });

        const f = input.filters || {};
        if (f.category) q = q.eq('category', f.category);
        if (f.status) q = q.eq('status', f.status);
        if (f.location) q = q.ilike('location', `%${f.location}%`);
        if (typeof f.for_sale === 'boolean') q = q.eq('for_sale', f.for_sale);
        if (typeof f.price_min === 'number') q = q.gte('current_value', f.price_min);
        if (typeof f.price_max === 'number') q = q.lte('current_value', f.price_max);
        if (typeof f.construction_year_min === 'number') q = q.gte('construction_year', f.construction_year_min);
        if (typeof f.construction_year_max === 'number') q = q.lte('construction_year', f.construction_year_max);

        if (input.q) {
          // simple text match on name/description
          q = q.or(`name.ilike.%${input.q}%,description.ilike.%${input.q}%`);
        }

        switch (input.sort) {
          case 'created_at_desc':
            q = q.order('created_at', { ascending: false });
            break;
          case 'current_value_desc':
            q = q.order('current_value', { ascending: false });
            break;
          case 'last_action_desc':
            q = q.order('last_action_date', { ascending: false });
            break;
          case 'construction_year_desc':
            q = q.order('construction_year', { ascending: false });
            break;
          case 'name_asc':
            q = q.order('name', { ascending: true });
            break;
        }

        const resp = await q.range(from, to);
        if (resp.error) throw resp.error;
        return { items: resp.data ?? [], total: resp.count ?? 0, page, page_size };
      },
    }),

    'items.get': tool({
      input: z.object({ id: z.number().int().positive() }).strict(),
      async handler(ctx, { id }) {
        const resp = await ctx.supabase.from('items').select('*').eq('id', id).single();
        if (resp.error) throw resp.error;
        return { item: resp.data };
      },
    }),

    'items.similar': tool({
      input: z.object({ query: z.string().min(1), k: z.number().int().min(1).max(50).default(10) }).strict(),
      async handler(ctx, { query, k }) {
        const openaiKey = process.env.OPENAI_API_KEY || '';
        let embedding: number[] | null = null;
        if (openaiKey) {
          const client = new OpenAI({ apiKey: openaiKey });
          const emb = await client.embeddings.create({ model: 'text-embedding-3-small', input: query });
          embedding = emb.data?.[0]?.embedding as unknown as number[];
        }

        if (embedding) {
          // Use pgvector <-> operator via RPC or PostgREST order embedding
          const resp = await ctx.supabase
            .from('items')
            .select('id,name,embedding')
            // PostgREST: order by embedding <-> query_embedding is not directly supported; use RPC
            .limit(k);

          if (resp.error) throw resp.error;
          // If server lacks RPC, fallback to cosine similarity client-side
          const scored = (resp.data || [])
            .filter((r: any) => Array.isArray(r.embedding))
            .map((r: any) => ({ id: r.id, name: r.name, score: cosineSim(embedding!, r.embedding) }))
            .sort((a, b) => b.score - a.score)
            .slice(0, k);
          return { matches: scored };
        }

        // Fallback text search
        const resp = await ctx.supabase
          .from('items')
          .select('id,name,description')
          .or(`name.ilike.%${query}%,description.ilike.%${query}%`)
          .limit(k);
        if (resp.error) throw resp.error;
        const matches = (resp.data || []).map((r: any) => ({ id: r.id, name: r.name, score: 0.0 }));
        return { matches };
      },
    }),

    'items.update_status': tool({
      input: z
        .object({
          id: z.number().int().positive(),
          patch: z
            .object({
              status: z.string().optional(),
              for_sale: z.boolean().optional(),
              sale_status: z.string().optional(),
              sale_progress: z.string().optional(),
              buyer_contact: z.string().optional(),
              intermediary: z.string().optional(),
              current_offer: moneySchema.optional(),
              commission_rate: z.number().min(0).max(1).optional(),
              last_action_date: dateSchema.optional(),
            })
            .strict(),
          dry_run: z.boolean().default(true),
          idempotency_key: z.string().optional(),
        })
        .strict(),
      async handler(ctx, { id, patch, dry_run }) {
        const updates: Record<string, any> = { ...patch, updated_at: new Date().toISOString() };

        if (patch.sale_status === 'sold') {
          updates.for_sale = false;
        }

        if (dry_run) {
          return { preview: { id, updates } };
        }

        const resp = await ctx.supabase.from('items').update(updates).eq('id', id).select('*').single();
        if (resp.error) throw resp.error;
        return { status: 'updated', item: resp.data };
      },
    }),

    'items.set_prices': tool({
      input: z
        .object({
          id: z.number().int().positive(),
          prices: z
            .object({
              current_value: moneySchema.optional(),
              asking_price: moneySchema.optional(),
              sold_price: moneySchema.optional(),
            })
            .strict(),
          effective_date: dateSchema.optional(),
          dry_run: z.boolean().default(true),
          idempotency_key: z.string().optional(),
        })
        .strict(),
      async handler(ctx, { id, prices, effective_date, dry_run, idempotency_key }) {
        const updates: Record<string, any> = { ...prices, updated_at: new Date().toISOString() };
        if (typeof prices.sold_price === 'number') {
          updates.for_sale = false;
          updates.sale_status = 'sold';
          updates.last_action_date = effective_date || new Date().toISOString().slice(0, 10);
        }

        if (dry_run) {
          return { preview: { id, updates } };
        }

        // Idempotence: (id, sold_price, effective_date)
        if (typeof prices.sold_price === 'number') {
          const key = idempotency_key || `${id}|${prices.sold_price}|${effective_date || 'today'}`;
          // If items has a column last_sale_key we can check; otherwise best-effort: if already sold_price equal and last_action_date matches effective_date
          const existing = await ctx.supabase.from('items').select('id,sale_status,sold_price,last_action_date').eq('id', id).single();
          if (!existing.error && existing.data) {
            const e = existing.data as any;
            const matchDate = (effective_date || new Date().toISOString().slice(0,10));
            if (e.sale_status === 'sold' && Number(e.sold_price) === prices.sold_price && String(e.last_action_date).slice(0,10) === matchDate) {
              return { status: 'updated', idempotent: true, item: existing.data };
            }
          }
        }

        const resp = await ctx.supabase.from('items').update(updates).eq('id', id).select('*').single();
        if (resp.error) throw resp.error;
        return { status: 'updated', item: resp.data };
      },
    }),
  };
}

function cosineSim(a: number[], b: number[]): number {
  const len = Math.min(a.length, b.length);
  let dot = 0,
    na = 0,
    nb = 0;
  for (let i = 0; i < len; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-12);
}


