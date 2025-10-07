## ChatGPT App (Hosted MCP Tools) – Squelette

Ce dossier explique comment déclarer le serveur MCP InventorySBO dans une App ChatGPT via Hosted MCP Tools.

### Pré-requis
- Déployer le MCP Server (`apps/mcp-server`) et récupérer son URL publique: `https://<TON_MCP_PUBLIC_URL>/mcp`.
- Les secrets Supabase restent côté serveur (ne pas exposer `SUPABASE_SERVICE_ROLE_KEY`).

### Étapes (ChatGPT App)
1. Crée une nouvelle App ChatGPT.
2. Ajoute un outil de type "Hosted MCP Tool".
3. Configure:
   - Label: `inventory-supabase`
   - URL: `https://<TON_MCP_PUBLIC_URL>/mcp`
   - Allowed tools:
     - `items.search`
     - `items.get`
     - `items.similar`
     - `items.update_status`
     - `items.set_prices`
     - `banking.classes.list`
     - `banking.summary`
     - `market.analyses.search`
     - `market.analyses.get`
     - `market.analyses.upsert`
     - `realestate.listings.search`
     - `trades.list`
     - `trades.record`
     - `trades.close`
     - `exports.generate`
   - Timeout: `120000` ms
4. Prompt système conseillé:
   - `Assistant portefeuille. N’invente pas de chiffres: utilise les outils.`

### Exemple d’appels (copier-coller dans ChatGPT)
```
{ "tool": "items.search", "input": { "q": "table", "page": 1, "page_size": 10 } }
```

```
{ "tool": "trades.record", "input": { "symbol": "AAPL", "direction": "long", "entry_date": "2025-10-07T10:00:00Z", "entry_price": 182.3, "idempotency_key": "abc-123" } }
```

### Notes
- `dry_run` par défaut sur les writes: renvoie `preview`. Rejouer avec `dry_run: false` pour confirmer.
- Possibilité d’impersonation par header `x-user-jwt` si RLS activée.


