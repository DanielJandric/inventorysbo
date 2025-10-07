## Agent Sample (OpenAI Agents + Hosted MCP Tools)

Demonstrates how to consume the Inventory MCP server with OpenAI Agents SDK using Hosted MCP Tools.

### Setup
1. Install deps: `pnpm -C apps/agent-sample install`
2. Edit `src/agent.ts` and set the MCP server URL.
3. Run: `pnpm -C apps/agent-sample dev`

### Flow example
- items.search then exports.generate (xlsx)
- items.set_prices with dry_run then confirmation
- trades.record with idempotency_key then trades.close


