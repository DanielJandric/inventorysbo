import { z } from 'zod';
import { datetimeSchema, moneySchema } from '../../lib/validation.ts';
import type { Registry } from '../index.js';
import { createHash } from 'crypto';

const directionEnum = z.enum(['long', 'short', 'call', 'put', 'spread', 'other']);

export function tradesTools(tool: <I extends z.ZodTypeAny, O>(def: { input: I; handler: any }) => any): Registry {
  return {
    'trades.list': tool({
      input: z
        .object({
          symbol: z.string().optional(),
          is_option: z.boolean().optional(),
          date_from: datetimeSchema.optional(),
          date_to: datetimeSchema.optional(),
          open_only: z.boolean().default(false),
        })
        .strict(),
      async handler(ctx, input) {
        let q = ctx.supabase.from('trades').select('*').order('entry_date', { ascending: false }).limit(500);
        if (input.symbol) q = q.eq('symbol', input.symbol);
        if (typeof input.is_option === 'boolean') q = q.eq('is_option', input.is_option);
        if (input.date_from) q = q.gte('entry_date', input.date_from);
        if (input.date_to) q = q.lte('entry_date', input.date_to);
        if (input.open_only) q = q.is('exit_date', null);
        const resp = await q;
        if (resp.error) throw resp.error;
        return { items: resp.data || [] };
      },
    }),

    'trades.record': tool({
      input: z
        .object({
          id: z.number().int().positive().optional(),
          idempotency_key: z.string().optional(),
          symbol: z.string(),
          direction: directionEnum,
          strategy: z.string().optional(),
          entry_date: datetimeSchema,
          entry_price: moneySchema.gt(0),
          stop_loss: moneySchema.optional(),
          take_profit: moneySchema.optional(),
          size: z.number().optional(),
          is_option: z.boolean().default(false),
          option_type: z.enum(['call', 'put']).optional(),
          expiration: z.string().optional(), // ISO date
          strike: moneySchema.optional(),
          multiplier: z.number().optional(),
          tags: z.array(z.string()).optional(),
          notes: z.string().optional(),
          dry_run: z.boolean().default(true),
        })
        .strict(),
      async handler(ctx, input) {
        if (input.is_option && !input.option_type) {
          throw Object.assign(new Error('option_type is required when is_option=true'), { statusCode: 400 });
        }

        const naturalKey = input.idempotency_key || hash(
          `${input.symbol}|${input.entry_date}|${input.entry_price}|${input.size ?? 0}`,
        );

        // Idempotence check
        const existing = await ctx.supabase
          .from('trades')
          .select('id')
          .eq('idempotency_key', naturalKey)
          .maybeSingle?.();

        if ((existing as any)?.data?.id) {
          return { status: 'recorded', id: (existing as any).data.id, idempotent: true };
        }

        const record: any = { ...input, idempotency_key: naturalKey };
        delete record.dry_run;
        delete record.id;
        delete record.idempotency_key; // will reassign below
        record.idempotency_key = naturalKey;

        if (input.dry_run) {
          return { preview: record };
        }

        const ins = await ctx.supabase.from('trades').insert(record).select('id').single();
        if (ins.error) throw ins.error;
        return { status: 'recorded', id: ins.data.id };
      },
    }),

    'trades.close': tool({
      input: z
        .object({ id: z.number().int().positive(), exit_date: datetimeSchema, exit_price: moneySchema.gt(0), dry_run: z.boolean().default(true) })
        .strict(),
      async handler(ctx, { id, exit_date, exit_price, dry_run }) {
        const updates: any = { exit_date, exit_price, updated_at: new Date().toISOString() };
        if (dry_run) return { preview: { id, updates } };
        const resp = await ctx.supabase.from('trades').update(updates).eq('id', id).select('id').single();
        if (resp.error) throw resp.error;
        return { status: 'closed', id };
      },
    }),
  };
}

function hash(s: string): string {
  return createHash('sha256').update(s).digest('hex');
}


