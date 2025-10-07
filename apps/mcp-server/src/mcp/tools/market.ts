import { z } from 'zod';
import { buildRange, datetimeSchema, paginationSchema } from '../../lib/validation.ts';
import type { Registry } from '../index.js';

export function marketTools(tool: <I extends z.ZodTypeAny, O>(def: { input: I; handler: any }) => any): Registry {
  return {
    'market.analyses.search': tool({
      input: z
        .object({
          analysis_type: z.string().optional(),
          date_from: datetimeSchema.optional(),
          date_to: datetimeSchema.optional(),
          min_confidence: z.number().min(0).max(1).optional(),
          ...paginationSchema.shape,
        })
        .strict(),
      async handler(ctx, input) {
        const { page, page_size } = input;
        const { from, to } = buildRange(page, page_size);
        let q = ctx.supabase.from('market_analyses').select('*', { count: 'exact' });
        if (input.analysis_type) q = q.eq('analysis_type', input.analysis_type);
        if (input.date_from) q = q.gte('timestamp', input.date_from);
        if (input.date_to) q = q.lte('timestamp', input.date_to);
        if (typeof input.min_confidence === 'number') q = q.gte('confidence_score', input.min_confidence);
        q = q.order('timestamp', { ascending: false }).range(from, to);
        const resp = await q;
        if (resp.error) throw resp.error;
        return { items: resp.data || [], total: resp.count ?? 0, page, page_size };
      },
    }),

    'market.analyses.get': tool({
      input: z.object({ id: z.number().int().positive() }).strict(),
      async handler(ctx, { id }) {
        const resp = await ctx.supabase.from('market_analyses').select('*').eq('id', id).single();
        if (resp.error) throw resp.error;
        return { analysis: resp.data };
      },
    }),

    'market.analyses.upsert': tool({
      input: z
        .object({
          timestamp: datetimeSchema.optional(),
          analysis_type: z.string(),
          summary: z.string(),
          key_points: z.array(z.string()).optional(),
          structured_data: z.record(z.any()).optional(),
          insights: z.record(z.any()).optional(),
          risks: z.record(z.any()).optional(),
          opportunities: z.record(z.any()).optional(),
          sources: z.array(z.string()).optional(),
          confidence_score: z.number().min(0).max(1).optional(),
          dry_run: z.boolean().default(false),
          idempotency_key: z.string().optional(),
        })
        .strict(),
      async handler(ctx, input) {
        const timestamp = input.timestamp || new Date().toISOString();
        const record = { ...input, timestamp } as any;
        delete record.dry_run;
        delete record.idempotency_key;

        if (input.dry_run) {
          return { preview: record };
        }

        // Idempotence using analysis_type + timestamp
        const existing = await ctx.supabase
          .from('market_analyses')
          .select('id')
          .eq('analysis_type', input.analysis_type)
          .eq('timestamp', timestamp)
          .maybeSingle?.();

        // Not all supabase-js versions have maybeSingle; fallback:
        let upsertId: number | undefined;
        if ((existing as any)?.data?.id) {
          upsertId = (existing as any).data.id;
          const resp = await ctx.supabase.from('market_analyses').update(record).eq('id', upsertId).select('id').single();
          if (resp.error) throw resp.error;
          return { status: 'upserted', id: resp.data.id };
        }

        const ins = await ctx.supabase.from('market_analyses').insert(record).select('id').single();
        if (ins.error) throw ins.error;
        return { status: 'upserted', id: ins.data.id };
      },
    }),
  };
}


