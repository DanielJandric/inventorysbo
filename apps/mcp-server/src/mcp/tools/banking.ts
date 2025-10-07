import { z } from 'zod';
import type { Registry } from '../index.js';

export function bankingTools(tool: <I extends z.ZodTypeAny, O>(def: { input: I; handler: any }) => any): Registry {
  return {
    'banking.classes.list': tool({
      input: z.object({ include_mapping: z.boolean().default(false) }).strict(),
      async handler(ctx, { include_mapping }) {
        const major = await ctx.supabase.from('banking_asset_classes_major').select('*').order('id');
        if (major.error) throw major.error;
        const minor = await ctx.supabase.from('banking_asset_classes_minor').select('*').order('id');
        if (minor.error) throw minor.error;
        let mapping: any[] = [];
        if (include_mapping) {
          const resp = await ctx.supabase.from('category_banking_mapping').select('*').order('original_category');
          if (resp.error) throw resp.error;
          mapping = resp.data || [];
        }
        return { major: major.data || [], minor: minor.data || [], mapping };
      },
    }),

    'banking.summary': tool({
      input: z.object({ major_class: z.string().optional(), minor_class: z.string().optional() }).strict(),
      async handler(ctx, { major_class, minor_class }) {
        let q = ctx.supabase.from('banking_asset_class_summary').select('*');
        if (major_class) q = q.eq('major_class', major_class);
        if (minor_class) q = q.eq('minor_class', minor_class);
        const resp = await q;
        if (resp.error) throw resp.error;
        return { items: resp.data || [] };
      },
    }),
  };
}


