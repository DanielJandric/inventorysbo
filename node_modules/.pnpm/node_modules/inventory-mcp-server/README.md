## InventorySBO MCP Server

Fastify server exposing MCP tools backed by Supabase. Validated with zod, audited with pino, and rate limited. Default port 8787.

### Setup
1. Copy `.env.example` to `.env` and fill:
   - `SUPABASE_URL=...`
   - `SUPABASE_SERVICE_ROLE_KEY=...` (server only)
   - `OPENAI_API_KEY=...` (for items.similar embeddings)
   - `PORT=8787`
   - `LOG_LEVEL=info`
2. Install deps: `pnpm -C apps/mcp-server install`
3. Dev: `pnpm -C apps/mcp-server dev`

Note: ensure `.env` is present. Do not expose `SUPABASE_SERVICE_ROLE_KEY` to clients.

### Endpoint
POST `/mcp` with body:
```json
{ "tool": "items.search", "input": { "filters": {}, "page": 1, "page_size": 50 } }
```

### Tools and sample payloads
- items.search
```json
{ "tool": "items.search", "input": { "q": "table", "filters": {"category": "furniture", "for_sale": true, "price_max": 5000}, "sort": "current_value_desc", "page": 1, "page_size": 20 } }
```
- items.get
```json
{ "tool": "items.get", "input": { "id": 123 } }
```
- items.similar
```json
{ "tool": "items.similar", "input": { "query": "chaise scandinave chêne", "k": 10 } }
```
- items.update_status (dry_run default true)
```json
{ "tool": "items.update_status", "input": { "id": 123, "patch": {"status": "negotiation", "commission_rate": 0.08}, "dry_run": true } }
```
- items.set_prices (sold, dry_run default true; idempotence on id,sold_price,effective_date)
```json
{ "tool": "items.set_prices", "input": { "id": 123, "prices": {"sold_price": 1200000}, "effective_date": "2025-10-07" } }
```
- banking.classes.list
```json
{ "tool": "banking.classes.list", "input": { "include_mapping": true } }
```
- banking.summary
```json
{ "tool": "banking.summary", "input": { "major_class": "Actifs réels" } }
```
- market.analyses.search
```json
{ "tool": "market.analyses.search", "input": { "analysis_type": "daily", "page": 1, "page_size": 10 } }
```
- market.analyses.get
```json
{ "tool": "market.analyses.get", "input": { "id": 42 } }
```
- market.analyses.upsert (dry-run)
```json
{ "tool": "market.analyses.upsert", "input": { "analysis_type": "daily", "summary": "Résumé", "dry_run": true } }
```
- realestate.listings.search
```json
{ "tool": "realestate.listings.search", "input": { "location": "Lausanne", "price_max": 1200000 } }
```
- trades.list
```json
{ "tool": "trades.list", "input": { "symbol": "AAPL", "open_only": true } }
```
- trades.record (idempotent, dry_run default true)
```json
{ "tool": "trades.record", "input": { "symbol": "AAPL", "direction": "long", "entry_date": "2025-10-07T10:00:00Z", "entry_price": 182.3, "size": 10, "idempotency_key": "abc-123" } }
```
- trades.close (dry_run default true)
```json
{ "tool": "trades.close", "input": { "id": 77, "exit_date": "2025-10-08T15:30:00Z", "exit_price": 190 } }
```
- exports.generate
```json
{ "tool": "exports.generate", "input": { "dataset": "items", "format": "xlsx" } }
```

### Security
- Inputs validated by zod; strict schemas.
- Dry-run supported on write tools.
- Idempotence keys on trades and natural keys for market analyses upsert.
- Audit logs with latency on start/end of each tool.
- Rate limit 60 req/min; 25s timeout.

### RLS & Impersonation
Requests may include a user JWT in header `x-user-jwt` to impersonate users under RLS. The server never exposes `SUPABASE_SERVICE_ROLE_KEY`.

### Dry-run confirmations
Write tools default to `dry_run: true`. Send the same payload with `dry_run: false` to apply after checking the preview. For `trades.record`, prefer providing `idempotency_key`.


