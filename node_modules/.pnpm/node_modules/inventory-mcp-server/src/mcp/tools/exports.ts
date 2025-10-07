import { z } from 'zod';
import type { Registry } from '../index.js';
import { Parser as Json2CsvParser } from 'json2csv';
import * as XLSX from 'xlsx';
import { mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';

export function exportsTools(tool: <I extends z.ZodTypeAny, O>(def: { input: I; handler: any }) => any): Registry {
  return {
    'exports.generate': tool({
      input: z
        .object({
          dataset: z.enum(['items', 'trades', 'market_analyses', 'banking_summary']),
          filters: z.record(z.any()).optional(),
          format: z.enum(['csv', 'xlsx', 'pdf']),
          columns: z.array(z.string()).optional(),
          dry_run: z.boolean().default(false),
        })
        .strict(),
      async handler(ctx, input) {
        const data = await fetchDataset(ctx, input.dataset, input.filters || {});
        const selected = input.columns && input.columns.length > 0 ? data.map((r: any) => pick(r, input.columns!)) : data;

        const dir = join(process.cwd(), 'exports');
        mkdirSync(dir, { recursive: true });
        const filenameBase = `${input.dataset}-${Date.now()}`;

        if (input.format === 'pdf') {
          const file = join(dir, `${filenameBase}.pdf`);
          writeFileSync(file, Buffer.from('%PDF-1.4\n% Stub PDF export. Implement real rendering as needed.'));
          return { status: 'ok', url: file };
        }

        if (input.format === 'csv') {
          const parser = new Json2CsvParser();
          const csv = parser.parse(selected);
          const file = join(dir, `${filenameBase}.csv`);
          writeFileSync(file, csv, 'utf8');
          return { status: 'ok', url: file };
        }

        // xlsx
        const ws = XLSX.utils.json_to_sheet(selected);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'data');
        const file = join(dir, `${filenameBase}.xlsx`);
        XLSX.writeFile(wb, file);
        return { status: 'ok', url: file };
      },
    }),
  };
}

async function fetchDataset(ctx: any, dataset: string, filters: Record<string, any>): Promise<any[]> {
  switch (dataset) {
    case 'items': {
      let q = ctx.supabase.from('items').select('*').order('created_at', { ascending: false }).limit(1000);
      if (filters?.status) q = q.eq('status', filters.status);
      const resp = await q;
      if (resp.error) throw resp.error;
      return resp.data || [];
    }
    case 'trades': {
      let q = ctx.supabase.from('trades').select('*').order('entry_date', { ascending: false }).limit(2000);
      if (filters?.symbol) q = q.eq('symbol', filters.symbol);
      const resp = await q;
      if (resp.error) throw resp.error;
      return resp.data || [];
    }
    case 'market_analyses': {
      const resp = await ctx.supabase.from('market_analyses').select('*').order('timestamp', { ascending: false }).limit(2000);
      if (resp.error) throw resp.error;
      return resp.data || [];
    }
    case 'banking_summary': {
      const resp = await ctx.supabase.from('banking_asset_class_summary').select('*').order('major_class').limit(5000);
      if (resp.error) throw resp.error;
      return resp.data || [];
    }
    default:
      return [];
  }
}

function pick(obj: any, keys: string[]) {
  const out: any = {};
  for (const k of keys) if (k in obj) out[k] = obj[k];
  return out;
}


