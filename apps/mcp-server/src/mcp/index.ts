import { z } from 'zod';
import type { SupabaseClient } from '../lib/supabase.js';

type ToolHandlerContext = { supabase: SupabaseClient; headers: Record<string, any> | undefined; signal: AbortSignal };

type ToolDef<I extends z.ZodTypeAny, O> = {
  input: I;
  handler: (ctx: ToolHandlerContext, input: z.infer<I>) => Promise<O>;
};

export type Registry = Record<string, ToolDef<any, any>>;

function defineTool<I extends z.ZodTypeAny, O>(def: ToolDef<I, O>): ToolDef<I, O> {
  return def;
}

import { itemsTools } from './tools/items.js';
import { bankingTools } from './tools/banking.js';
import { marketTools } from './tools/market.js';
import { realestateTools } from './tools/realestate.js';
import { tradesTools } from './tools/trades.js';
import { exportsTools } from './tools/exports.js';

export const registry: Registry = {
  ...itemsTools(defineTool),
  ...bankingTools(defineTool),
  ...marketTools(defineTool),
  ...realestateTools(defineTool),
  ...tradesTools(defineTool),
  ...exportsTools(defineTool),
};


