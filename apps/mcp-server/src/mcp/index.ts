import { z } from 'zod';
import type { SupabaseClient } from '../lib/supabase.ts';

type ToolHandlerContext = { supabase: SupabaseClient; headers: Record<string, any> | undefined; signal: AbortSignal };

type ToolDef<I extends z.ZodTypeAny, O> = {
  input: I;
  handler: (ctx: ToolHandlerContext, input: z.infer<I>) => Promise<O>;
};

export type Registry = Record<string, ToolDef<any, any>>;

function defineTool<I extends z.ZodTypeAny, O>(def: ToolDef<I, O>): ToolDef<I, O> {
  return def;
}

import { itemsTools } from './tools/items.ts';
import { bankingTools } from './tools/banking.ts';
import { marketTools } from './tools/market.ts';
import { realestateTools } from './tools/realestate.ts';
import { tradesTools } from './tools/trades.ts';
import { exportsTools } from './tools/exports.ts';

export const registry: Registry = {
  ...itemsTools(defineTool),
  ...bankingTools(defineTool),
  ...marketTools(defineTool),
  ...realestateTools(defineTool),
  ...tradesTools(defineTool),
  ...exportsTools(defineTool),
};


