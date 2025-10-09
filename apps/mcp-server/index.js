const http = require('http');
const { createClient } = require('@supabase/supabase-js');
const { Parser: Json2CsvParser } = require('json2csv');
const XLSX = require('xlsx');
const { mkdirSync, writeFileSync } = require('fs');
const { join } = require('path');

const PORT = Number(process.env.PORT || 8787);

function sendJson(res, statusCode, data, extraHeaders) {
  const headers = Object.assign(
    {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-cache',
    },
    extraHeaders || {}
  );
  res.writeHead(statusCode, headers);
  res.end(JSON.stringify(data));
}

function parseJsonBody(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', (chunk) => {
      raw += chunk;
      if (raw.length > 2 * 1024 * 1024) {
        reject(new Error('Payload too large'));
        req.destroy();
      }
    });
    req.on('end', () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

function createSupabaseClient(headers) {
  const supabaseUrl = process.env.SUPABASE_URL || '';
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
  if (!supabaseUrl || !supabaseKey) {
    const err = new Error('Missing Supabase credentials');
    err.statusCode = 500;
    throw err;
  }
  const headersLower = {};
  if (headers && typeof headers === 'object') {
    for (const [k, v] of Object.entries(headers)) headersLower[String(k).toLowerCase()] = String(v);
  }
  const userJwt = headersLower['x-user-jwt'];
  const impersonate = typeof userJwt === 'string' && userJwt.trim().length > 0;
  return createClient(supabaseUrl, supabaseKey, {
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
    global: impersonate ? { headers: { Authorization: `Bearer ${userJwt}` } } : undefined,
  });
}

async function handleItemsSearch(ctx, input) {
  const page = Number(input.page || 1) || 1;
  const page_size = Math.min(Math.max(Number(input.page_size || 50) || 50, 1), 200);
  const from = (page - 1) * page_size;
  const to = from + page_size - 1;
  let q = ctx.supabase.from('items').select('*', { count: 'exact' });
  const f = (input.filters && typeof input.filters === 'object') ? input.filters : {};
  if (f.category) q = q.eq('category', f.category);
  if (f.status) q = q.eq('status', f.status);
  if (f.sale_status) q = q.eq('sale_status', f.sale_status);
  if (String(f.exclude_sold || 'false') === 'true') q = q.neq('sale_status', 'sold');
  if (typeof f.for_sale === 'boolean') q = q.eq('for_sale', f.for_sale);
  if (f.location) q = q.ilike('location', `%${f.location}%`);
  if (typeof f.price_min === 'number') q = q.gte('current_value', f.price_min);
  if (typeof f.price_max === 'number') q = q.lte('current_value', f.price_max);
  if (typeof f.construction_year_min === 'number') q = q.gte('construction_year', f.construction_year_min);
  if (typeof f.construction_year_max === 'number') q = q.lte('construction_year', f.construction_year_max);
  if (input.q) q = q.or(`name.ilike.%${input.q}%,description.ilike.%${input.q}%`);
  switch (input.sort) {
    case 'current_value_desc': q = q.order('current_value', { ascending: false }); break;
    case 'last_action_desc': q = q.order('last_action_date', { ascending: false }); break;
    case 'construction_year_desc': q = q.order('construction_year', { ascending: false }); break;
    case 'name_asc': q = q.order('name', { ascending: true }); break;
    default: q = q.order('created_at', { ascending: false });
  }
  const resp = await q.range(from, to);
  if (resp.error) throw resp.error;
  return { items: resp.data || [], total: resp.count ?? 0, page, page_size };
}

async function handleItemsGet(ctx, input) {
  const id = Number(input.id);
  const resp = await ctx.supabase.from('items').select('*').eq('id', id).single();
  if (resp.error) throw resp.error;
  return { item: resp.data };
}

async function handleItemsSimilar(ctx, input) {
  const query = String(input.query || '').trim();
  const k = Math.min(Math.max(Number(input.k || 10) || 10, 1), 50);
  const resp = await ctx.supabase
    .from('items')
    .select('id,name,description')
    .or(`name.ilike.%${query}%,description.ilike.%${query}%`)
    .limit(k);
  if (resp.error) throw resp.error;
  const matches = (resp.data || []).map(r => ({ id: r.id, name: r.name, score: 0.0 }));
  return { matches };
}

async function handleItemsUpdateStatus(ctx, input) {
  const id = Number(input.id);
  const patch = (input.patch && typeof input.patch === 'object') ? { ...input.patch } : {};
  const updates = { ...patch, updated_at: new Date().toISOString() };
  if (patch.sale_status === 'sold') updates.for_sale = false;
  if (String(input.dry_run || 'false') === 'true') return { preview: { id, updates } };
  const resp = await ctx.supabase.from('items').update(updates).eq('id', id).select('*').single();
  if (resp.error) throw resp.error;
  return { status: 'updated', item: resp.data };
}

async function handleItemsSetPrices(ctx, input) {
  const id = Number(input.id);
  const prices = (input.prices && typeof input.prices === 'object') ? { ...input.prices } : {};
  const effective_date = input.effective_date || null;
  const updates = { ...prices, updated_at: new Date().toISOString() };
  if (typeof prices.sold_price === 'number') {
    updates.for_sale = false;
    updates.sale_status = 'sold';
    updates.last_action_date = effective_date || new Date().toISOString().slice(0,10);
  }
  if (String(input.dry_run || 'false') === 'true') return { preview: { id, updates } };
  const resp = await ctx.supabase.from('items').update(updates).eq('id', id).select('*').single();
  if (resp.error) throw resp.error;
  return { status: 'updated', item: resp.data };
}

async function handleItemsCreate(ctx, input) {
  const record = (input && typeof input === 'object') ? { ...input } : {};
  // guard minimal: name or category required
  if (!record.name && !record.category) {
    const e = new Error('Missing minimal fields: name or category'); e.statusCode = 400; throw e;
  }
  // Auto fields
  record.created_at = new Date().toISOString();
  if (record.sale_status === 'sold') record.for_sale = false;
  const resp = await ctx.supabase.from('items').insert(record).select('*').single();
  if (resp.error) throw resp.error;
  return { status: 'created', item: resp.data };
}

async function handleItemsSummary(ctx, input) {
  const filters = (input && typeof input === 'object' ? input.filters : null) || {};
  // Sélection minimale (certaines bases n'ont pas brand/model)
  let q = ctx.supabase.from('items').select('id,category,status,for_sale,sale_status');
  if (filters.category) q = q.eq('category', filters.category);
  if (filters.status) q = q.eq('status', filters.status);
  if (filters.sale_status) q = q.eq('sale_status', filters.sale_status);
  if (String(filters.exclude_sold || 'false') === 'true') q = q.neq('sale_status', 'sold');
  if (typeof filters.for_sale === 'boolean') q = q.eq('for_sale', filters.for_sale);
  const resp = await q;
  if (resp.error) throw resp.error;
  const rows = resp.data || [];
  const total = rows.length;
  const byCategory = {};
  for (const r of rows) {
    const c = r.category || 'Autres';
    byCategory[c] = (byCategory[c] || 0) + 1;
  }
  const onSale = rows.filter(r => r.for_sale === true).length;
  const byStatus = {};
  for (const r of rows) {
    const s = r.status || 'unknown';
    byStatus[s] = (byStatus[s] || 0) + 1;
  }
  return { total, on_sale: onSale, by_category: byCategory, by_status: byStatus };
}

async function handleBankingClassesList(ctx, input) {
  const major = await ctx.supabase.from('banking_asset_classes_major').select('*').order('id');
  if (major.error) throw major.error;
  const minor = await ctx.supabase.from('banking_asset_classes_minor').select('*').order('id');
  if (minor.error) throw minor.error;
  let mapping = [];
  if (String(input.include_mapping || 'false') === 'true') {
    const resp = await ctx.supabase.from('category_banking_mapping').select('*').order('original_category');
    if (resp.error) throw resp.error;
    mapping = resp.data || [];
  }
  return { major: major.data || [], minor: minor.data || [], mapping };
}

async function handleBankingSummary(ctx, input) {
  let q = ctx.supabase.from('banking_asset_class_summary').select('*');
  if (input.major_class) q = q.eq('major_class', input.major_class);
  if (input.minor_class) q = q.eq('minor_class', input.minor_class);
  const resp = await q;
  if (resp.error) throw resp.error;
  return { items: resp.data || [] };
}

async function handleMarketSearch(ctx, input) {
  const page = Number(input.page || 1) || 1;
  const page_size = Math.min(Math.max(Number(input.page_size || 50) || 50, 1), 200);
  const from = (page - 1) * page_size;
  const to = from + page_size - 1;
  let q = ctx.supabase.from('market_analyses').select('*', { count: 'exact' });
  if (input.analysis_type) q = q.eq('analysis_type', input.analysis_type);
  if (input.date_from) q = q.gte('timestamp', input.date_from);
  if (input.date_to) q = q.lte('timestamp', input.date_to);
  if (typeof input.min_confidence === 'number') q = q.gte('confidence_score', input.min_confidence);
  q = q.order('timestamp', { ascending: false }).range(from, to);
  const resp = await q;
  if (resp.error) throw resp.error;
  return { items: resp.data || [], total: resp.count ?? 0, page, page_size };
}

async function handleMarketGet(ctx, input) {
  const id = Number(input.id);
  const resp = await ctx.supabase.from('market_analyses').select('*').eq('id', id).single();
  if (resp.error) throw resp.error;
  return { analysis: resp.data };
}

async function handleMarketUpsert(ctx, input) {
  const timestamp = input.timestamp || new Date().toISOString();
  const record = { ...input, timestamp };
  delete record.dry_run;
  delete record.idempotency_key;
  if (String(input.dry_run || 'false') === 'true') return { preview: record };
  const existing = await ctx.supabase
    .from('market_analyses')
    .select('id')
    .eq('analysis_type', input.analysis_type)
    .eq('timestamp', timestamp)
    .limit(1);
  const found = (existing.data && existing.data[0] && existing.data[0].id) ? existing.data[0].id : undefined;
  if (found) {
    const upd = await ctx.supabase.from('market_analyses').update(record).eq('id', found).select('id').single();
    if (upd.error) throw upd.error;
    return { status: 'upserted', id: upd.data.id };
  }
  const ins = await ctx.supabase.from('market_analyses').insert(record).select('id').single();
  if (ins.error) throw ins.error;
  return { status: 'upserted', id: ins.data.id };
}

async function handleRealEstateSearch(ctx, input) {
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
}

function sha256Hex(s) {
  const crypto = require('crypto');
  return crypto.createHash('sha256').update(s).digest('hex');
}

// New handlers
async function handleItemsTopByValue(ctx, input) {
  const category = input.category || null;
  const page_size = Math.min(Math.max(Number(input.page_size || 10) || 10, 1), 50);
  let q = ctx.supabase.from('items').select('*').order('current_value', { ascending: false }).limit(page_size);
  if (category) q = q.eq('category', category);
  if (String(input.exclude_sold || 'true') === 'true') q = q.neq('sale_status', 'sold');
  const resp = await q;
  if (resp.error) throw resp.error;
  return { items: resp.data || [] };
}

async function handleChatsList(ctx, input) {
  const resp = await ctx.supabase.from('chats').select('id,title,created_at').order('created_at', { ascending: false }).limit(200);
  if (resp.error) throw resp.error;
  return { chats: resp.data || [] };
}

async function handleMessagesList(ctx, input) {
  const chat_id = input.chat_id;
  if (!chat_id) {
    const e = new Error('chat_id is required'); e.statusCode = 400; throw e;
  }
  const resp = await ctx.supabase.from('messages').select('id,chat_id,role,content,created_at').eq('chat_id', chat_id).order('created_at', { ascending: true }).limit(1000);
  if (resp.error) throw resp.error;
  return { messages: resp.data || [] };
}

async function handleMessagesAdd(ctx, input) {
  const record = { chat_id: input.chat_id, role: input.role, content: input.content };
  if (!record.chat_id || !record.role || !record.content) {
    const e = new Error('chat_id, role, content are required'); e.statusCode = 400; throw e;
  }
  const resp = await ctx.supabase.from('messages').insert(record).select('id,created_at').single();
  if (resp.error) throw resp.error;
  return { status: 'inserted', id: resp.data.id, created_at: resp.data.created_at };
}

async function handleSchemaTables(ctx, input) {
  const resp = await ctx.supabase.rpc('http_get_tables');
  if (resp.error) {
    // Fallback simple en interrogeant pg_catalog si rpc absent
    const sql = `select table_name from information_schema.tables where table_schema = 'public' order by table_name`;
    const { data, error } = await ctx.supabase.rpc('exec_sql', { q: sql });
    if (error) throw error;
    return { tables: data || [] };
  }
  return { tables: resp.data || [] };
}

async function handleSchemaColumns(ctx, input) {
  const table = input.table;
  if (!table) { const e = new Error('table is required'); e.statusCode = 400; throw e; }
  const sql = `select column_name, data_type from information_schema.columns where table_schema = 'public' and table_name = '${table}' order by ordinal_position`;
  const { data, error } = await ctx.supabase.rpc('exec_sql', { q: sql });
  if (error) throw error;
  return { columns: data || [] };
}

async function handleDbQuery(ctx, input) {
  const table = input.table;
  if (!table) { const e = new Error('table is required'); e.statusCode = 400; throw e; }
  // Whitelist simple de tables usuelles
  const allowed = new Set(['items','trades','market_analyses','real_estate_listings','banking_asset_classes_major','banking_asset_classes_minor','banking_asset_class_summary','chats','messages']);
  if (!allowed.has(table)) { const e = new Error('table not allowed'); e.statusCode = 403; throw e; }
  let q = ctx.supabase.from(table).select('*');
  const filters = (input.filters && typeof input.filters === 'object') ? input.filters : {};
  for (const [k, v] of Object.entries(filters)) {
    if (v === null) q = q.is(k, null);
    else q = q.eq(k, v);
  }
  if (input.order_by) q = q.order(input.order_by, { ascending: input.ascending !== false });
  if (input.limit) q = q.limit(Math.min(Math.max(Number(input.limit) || 50, 1), 200));
  const resp = await q;
  if (resp.error) throw resp.error;
  return { rows: resp.data || [] };
}

function validateTableName(name) {
  return typeof name === 'string' && /^[A-Za-z0-9_]+$/.test(name);
}

// Generic, unrestricted helpers over public schema
async function handleDbSelect(ctx, input) {
  const table = input.table;
  if (!validateTableName(table)) { const e = new Error('invalid table'); e.statusCode = 400; throw e; }
  const columns = typeof input.columns === 'string' && input.columns.trim() ? input.columns : '*';
  let q = ctx.supabase.from(table).select(columns, { count: 'exact' });
  const filters = (input.filters && typeof input.filters === 'object') ? input.filters : {};
  for (const [k, v] of Object.entries(filters)) {
    if (v === null) q = q.is(k, null); else q = q.eq(k, v);
  }
  const ilike = (input.ilike && typeof input.ilike === 'object') ? input.ilike : {};
  for (const [k, v] of Object.entries(ilike)) {
    if (typeof v === 'string') q = q.ilike(k, v);
  }
  if (Array.isArray(input.order_by)) {
    for (const ob of input.order_by) {
      if (typeof ob === 'string') q = q.order(ob, { ascending: input.ascending !== false });
      else if (ob && typeof ob === 'object' && ob.column) q = q.order(ob.column, { ascending: ob.ascending !== false, nullsFirst: !!ob.nullsFirst });
    }
  } else if (input.order_by) {
    q = q.order(input.order_by, { ascending: input.ascending !== false });
  }
  if (input.limit) q = q.limit(Math.min(Math.max(Number(input.limit) || 100, 1), 2000));
  if (input.range && typeof input.range === 'object') {
    const from = Math.max(Number(input.range.from) || 0, 0);
    const to = Math.max(Number(input.range.to) || (from + 99), from);
    q = q.range(from, to);
  }
  const resp = await q;
  if (resp.error) throw resp.error;
  return { rows: resp.data || [], total: resp.count ?? null };
}

async function handleDbInsert(ctx, input) {
  const table = input.table;
  if (!validateTableName(table)) { const e = new Error('invalid table'); e.statusCode = 400; throw e; }
  const records = Array.isArray(input.records) ? input.records : (input.record ? [input.record] : []);
  if (!records.length) { const e = new Error('records (array) or record is required'); e.statusCode = 400; throw e; }
  const resp = await ctx.supabase.from(table).insert(records).select('*');
  if (resp.error) throw resp.error;
  return { inserted: resp.data || [], count: Array.isArray(resp.data) ? resp.data.length : 0 };
}

async function handleDbUpdate(ctx, input) {
  const table = input.table;
  if (!validateTableName(table)) { const e = new Error('invalid table'); e.statusCode = 400; throw e; }
  const match = (input.match && typeof input.match === 'object') ? input.match : null;
  const patch = (input.patch && typeof input.patch === 'object') ? input.patch : null;
  if (!match || !patch) { const e = new Error('match and patch are required'); e.statusCode = 400; throw e; }
  let q = ctx.supabase.from(table).update(patch);
  for (const [k, v] of Object.entries(match)) q = q.eq(k, v);
  if (input.limit) q = q.limit(Math.min(Math.max(Number(input.limit) || 100, 1), 2000));
  q = q.select('*');
  const resp = await q;
  if (resp.error) throw resp.error;
  return { updated: resp.data || [], count: Array.isArray(resp.data) ? resp.data.length : 0 };
}

async function handleDbDelete(ctx, input) {
  const table = input.table;
  if (!validateTableName(table)) { const e = new Error('invalid table'); e.statusCode = 400; throw e; }
  const match = (input.match && typeof input.match === 'object') ? input.match : null;
  if (!match) { const e = new Error('match is required'); e.statusCode = 400; throw e; }
  let q = ctx.supabase.from(table).delete();
  for (const [k, v] of Object.entries(match)) q = q.eq(k, v);
  q = q.select('*');
  const resp = await q;
  if (resp.error) throw resp.error;
  return { deleted: resp.data || [], count: Array.isArray(resp.data) ? resp.data.length : 0 };
}
async function handleTradesList(ctx, input) {
  let q = ctx.supabase.from('trades').select('*').order('entry_date', { ascending: false }).limit(500);
  if (input.symbol) q = q.eq('symbol', input.symbol);
  if (typeof input.is_option === 'boolean') q = q.eq('is_option', input.is_option);
  if (input.date_from) q = q.gte('entry_date', input.date_from);
  if (input.date_to) q = q.lte('entry_date', input.date_to);
  if (String(input.open_only || 'false') === 'true') q = q.is('exit_date', null);
  const resp = await q;
  if (resp.error) throw resp.error;
  return { items: resp.data || [] };
}

async function handleTradesRecord(ctx, input) {
  if (String(input.is_option || 'false') === 'true' && !input.option_type) {
    const e = new Error('option_type is required when is_option=true');
    e.statusCode = 400;
    throw e;
  }
  const naturalKey = String(input.idempotency_key || sha256Hex(`${input.symbol}|${input.entry_date}|${input.entry_price}|${input.size || 0}`));
  const existing = await ctx.supabase.from('trades').select('id').eq('idempotency_key', naturalKey).limit(1);
  const found = (existing.data && existing.data[0] && existing.data[0].id) ? existing.data[0].id : undefined;
  if (found) return { status: 'recorded', id: found, idempotent: true };
  const record = { ...input, idempotency_key: naturalKey };
  delete record.dry_run;
  delete record.id;
  if (String(input.dry_run || 'true') === 'true') return { preview: record };
  const ins = await ctx.supabase.from('trades').insert(record).select('id').single();
  if (ins.error) throw ins.error;
  return { status: 'recorded', id: ins.data.id };
}

async function handleTradesClose(ctx, input) {
  const id = Number(input.id);
  const updates = { exit_date: input.exit_date, exit_price: input.exit_price, updated_at: new Date().toISOString() };
  if (String(input.dry_run || 'true') === 'true') return { preview: { id, updates } };
  const resp = await ctx.supabase.from('trades').update(updates).eq('id', id).select('id').single();
  if (resp.error) throw resp.error;
  return { status: 'closed', id };
}

async function fetchDataset(ctx, dataset, filters) {
  switch (dataset) {
    case 'items': {
      let q = ctx.supabase.from('items').select('*').order('created_at', { ascending: false }).limit(1000);
      if (filters && filters.status) q = q.eq('status', filters.status);
      const resp = await q; if (resp.error) throw resp.error; return resp.data || [];
    }
    case 'trades': {
      let q = ctx.supabase.from('trades').select('*').order('entry_date', { ascending: false }).limit(2000);
      if (filters && filters.symbol) q = q.eq('symbol', filters.symbol);
      const resp = await q; if (resp.error) throw resp.error; return resp.data || [];
    }
    case 'market_analyses': {
      const resp = await ctx.supabase.from('market_analyses').select('*').order('timestamp', { ascending: false }).limit(2000);
      if (resp.error) throw resp.error; return resp.data || [];
    }
    case 'banking_summary': {
      const resp = await ctx.supabase.from('banking_asset_class_summary').select('*').order('major_class').limit(5000);
      if (resp.error) throw resp.error; return resp.data || [];
    }
    default:
      return [];
  }
}

async function handleExportsGenerate(ctx, input) {
  const dataset = String(input.dataset);
  const format = String(input.format);
  const filters = (input.filters && typeof input.filters === 'object') ? input.filters : {};
  const columns = Array.isArray(input.columns) ? input.columns : null;
  const data = await fetchDataset(ctx, dataset, filters);
  const selected = columns && columns.length > 0 ? data.map(r => {
    const out = {}; for (const k of columns) if (k in r) out[k] = r[k]; return out;
  }) : data;
  const dir = join(process.cwd(), 'exports');
  mkdirSync(dir, { recursive: true });
  const filenameBase = `${dataset}-${Date.now()}`;
  if (format === 'pdf') {
    const file = join(dir, `${filenameBase}.pdf`);
    writeFileSync(file, Buffer.from('%PDF-1.4\n% Stub PDF export.'));
    return { status: 'ok', url: file };
  }
  if (format === 'csv') {
    const parser = new Json2CsvParser();
    const csv = parser.parse(selected);
    const file = join(dir, `${filenameBase}.csv`);
    writeFileSync(file, csv, 'utf8');
    return { status: 'ok', url: file };
  }
  const ws = XLSX.utils.json_to_sheet(selected);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'data');
  const file = join(dir, `${filenameBase}.xlsx`);
  XLSX.writeFile(wb, file);
  return { status: 'ok', url: file };
}

const registry = {
  'items.search': handleItemsSearch,
  'items.get': handleItemsGet,
  'items.similar': handleItemsSimilar,
  'items.update_status': handleItemsUpdateStatus,
  'items.set_prices': handleItemsSetPrices,
  'items.summary': handleItemsSummary,
  'items.create': handleItemsCreate,
  // New items helpers
  'items.top_by_value': handleItemsTopByValue,
  'banking.classes.list': handleBankingClassesList,
  'banking.summary': handleBankingSummary,
  'market.analyses.search': handleMarketSearch,
  'market.analyses.get': handleMarketGet,
  'market.analyses.upsert': handleMarketUpsert,
  'realestate.listings.search': handleRealEstateSearch,
  'trades.list': handleTradesList,
  'trades.record': handleTradesRecord,
  'trades.close': handleTradesClose,
  // Chat persistence helpers
  'chats.list': handleChatsList,
  'messages.list': handleMessagesList,
  'messages.add': handleMessagesAdd,
  // Generic DB tools
  'schema.tables': handleSchemaTables,
  'schema.columns': handleSchemaColumns,
  'db.query': handleDbQuery,
  // Unrestricted public schema helpers
  'db.select': handleDbSelect,
  'db.insert': handleDbInsert,
  'db.update': handleDbUpdate,
  'db.delete': handleDbDelete,
  'exports.generate': handleExportsGenerate,
};

function resolveToolName(name) {
  if (!name) return null;
  const n = String(name);
  if (registry[n]) return n;
  const dotted = n.replace(/-/g, '.');
  if (registry[dotted]) return dotted;
  return null;
}

function buildToolList() {
  const descriptions = {
    'items.search': 'Rechercher des items avec filtres et pagination.',
    'items.get': 'Récupérer un item par id.',
    'items.similar': 'Trouver des items similaires par texte.',
    'items.update_status': "Mettre à jour le statut d'un item.",
    'items.set_prices': "Mettre à jour les prix et statut d'un item.",
    'items.summary': 'Résumé agrégé des items (par catégorie, statut).',
    'items.create': "Créer un nouvel item (record: {...}).",
    'items.top_by_value': 'Top items par valeur (option catégorie, hors vendus).',
    'banking.classes.list': 'Lister les classes d’actifs bancaires (major/minor).',
    'banking.summary': 'Résumé agrégé des classes bancaires.',
    'market.analyses.search': 'Rechercher des analyses de marché.',
    'market.analyses.get': 'Obtenir une analyse de marché par id.',
    'market.analyses.upsert': 'Insérer ou mettre à jour une analyse de marché.',
    'realestate.listings.search': 'Rechercher des annonces immobilières.',
    'trades.list': 'Lister les transactions.',
    'trades.record': 'Enregistrer une nouvelle transaction.',
    'trades.close': 'Clôturer une transaction.',
    'chats.list': 'Lister les chats (id, title, created_at).',
    'messages.list': 'Lister les messages d’un chat (ordre chronologique).',
    'messages.add': 'Ajouter un message (chat_id, role, content).',
    'schema.tables': 'Lister les tables (public).',
    'schema.columns': 'Lister les colonnes pour une table donnée.',
    'db.query': 'Requête générique (table whitelist), select/filters/order/limit.',
    'db.select': 'Sélection générique (toutes tables publiques): table, columns, filters, order, limit.',
    'db.insert': 'Insertion générique: table, records[].',
    'db.update': 'Mise à jour générique: table, match{}, patch{}, limit?',
    'db.delete': 'Suppression générique: table, match{}, limit?',
    'exports.generate': 'Générer un export de données (csv/xlsx/pdf).',
  };
  return Object.keys(registry).map((origName) => {
    // Tools names must match ^[a-zA-Z0-9_-]+$ for Agents SDK
    const safeName = String(origName).replace(/[^A-Za-z0-9_-]/g, '-');
    const name = safeName.replace(/\.+/g, '-');
    const tool = {
      name,
      inputSchema: { type: 'object', additionalProperties: true },
    };
    // Optionally attach a very short description to minimize token usage
    const d = descriptions[origName] || '';
    if (d && d.length <= 40) tool.description = d;
    return tool;
  });
}

const server = http.createServer(async (req, res) => {
  const { method, url } = req;

  if (method === 'GET' && url === '/health') {
    return sendJson(res, 200, { ok: true });
  }

  // Minimal MCP tool listing for Agents SDK HostedMCPTool and Streamable MCP
  if (method === 'GET') {
    console.log(`[mcp] discovery GET ${url}`);
    // Common discovery endpoints
    if (url === '/mcp/tools' || url === '/mcp/list_tools' || url === '/mcp/list-tools' || url === '/tools' || url === '/mcp') {
      return sendJson(res, 200, { tools: buildToolList() });
    }
    // Some SDKs request per-server label paths like /mcp/servers/<label>/tools
    let match = url.match(/^\/mcp\/servers\/[^/]+\/(tools|list_tools|list-tools)\/?$/);
    if (match) {
      return sendJson(res, 200, { tools: buildToolList() });
    }
    // Extremely tolerant: any path that ends with tools/list_tools/list-tools
    const tail = url.split('?')[0];
    if (/(^|\/)tools\/?$/.test(tail) || /(^|\/)list_tools\/?$/.test(tail) || /(^|\/)list-tools\/?$/.test(tail)) {
      return sendJson(res, 200, { tools: buildToolList() });
    }
    // Also accept non-prefixed server paths (some clients omit /mcp)
    match = url.match(/^\/servers\/[^/]+\/(tools|list_tools|list-tools)\/?$/);
    if (match) {
      return sendJson(res, 200, { tools: buildToolList() });
    }
  }

  if (method === 'POST' && (url === '/mcp' || url === '/mcp/invoke' || url === '/invoke' || url === '/call')) {
    console.log(`[mcp] invoke ${url}`);
    const start = Date.now();
    try {
      const body = await parseJsonBody(req);
      console.log('[mcp] body', JSON.stringify(body).slice(0, 500));
      // Minimal JSON-RPC support for Cursor MCP client
      if (body && body.jsonrpc === '2.0' && typeof body.method === 'string') {
        const rpcId = body.id ?? null;
        const methodName = String(body.method);
        const params = (body.params && typeof body.params === 'object') ? body.params : {};
        if (methodName === 'initialize') {
          // Return capability objects (not booleans) per MCP spec
          const result = {
            capabilities: { tools: {}, prompts: {}, resources: {}, logging: {} },
            protocolVersion: '2025-06-18',
            serverInfo: { name: 'inventory_mcp', version: '1.0.0' },
          };
          const latency = Date.now() - start;
          return sendJson(res, 200, { jsonrpc: '2.0', id: rpcId, result, meta: { latencyMs: latency } });
        }
        if (methodName === 'tools/list') {
          const tools = buildToolList();
          const latency = Date.now() - start;
          return sendJson(res, 200, { jsonrpc: '2.0', id: rpcId, result: { tools }, meta: { latencyMs: latency } });
        }
        if (methodName === 'tools/call') {
          const toolName = params.name || params.tool || params.method;
          const args = params.arguments || params.args || params.params || {};
          if (!toolName || typeof toolName !== 'string') {
            return sendJson(res, 400, { jsonrpc: '2.0', id: rpcId, error: { code: -32602, message: 'Missing tool name' } });
          }
          const resolved = resolveToolName(toolName);
          const handler = resolved ? registry[resolved] : null;
          if (!handler) {
            return sendJson(res, 404, { jsonrpc: '2.0', id: rpcId, error: { code: -32601, message: `Unknown tool: ${toolName}` } });
          }
          const supabase = createSupabaseClient(req.headers);
          const out = await handler({ supabase, headers: req.headers }, args);
          const latency = Date.now() - start;
          // Wrap as simple content response (compatible with many clients)
          return sendJson(res, 200, { jsonrpc: '2.0', id: rpcId, result: { content: [{ type: 'text', text: JSON.stringify(out) }] }, meta: { latencyMs: latency } });
        }
        // Unknown JSON-RPC method
        return sendJson(res, 404, { jsonrpc: '2.0', id: rpcId, error: { code: -32601, message: `Unknown method: ${methodName}` } });
      }
      if (!body || typeof body !== 'object') {
        return sendJson(res, 400, { ok: false, error: 'Invalid JSON body' });
      }

      const toolName = body.tool || body.name || body.method;
      const args = body.input || body.arguments || body.params || body.args || {};
  if (!toolName || typeof toolName !== 'string') {
        return sendJson(res, 400, { ok: false, error: 'Missing tool name' });
      }
      const resolved = resolveToolName(toolName);
      const handler = resolved ? registry[resolved] : null;
      if (!handler) {
        return sendJson(res, 404, { ok: false, error: `Unknown tool: ${toolName}` });
      }

      const supabase = createSupabaseClient(req.headers);
      const out = await handler({ supabase, headers: req.headers }, args);
  const latency = Date.now() - start;
      console.log(`[mcp] done ${toolName} in ${latency}ms`);
      return sendJson(res, 200, { ok: true, tool: toolName, result: out }, { 'x-latency-ms': String(latency) });
    } catch (err) {
      const status = err && err.statusCode ? Number(err.statusCode) : 400;
      const message = err && err.message ? String(err.message) : 'Bad Request';
      console.error('[mcp] error', status, message);
      return sendJson(res, status, { ok: false, error: message });
    }
  }

  sendJson(res, 404, { ok: false, error: 'Not Found' });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`MCP server listening on :${PORT}`);
});

module.exports = server;

