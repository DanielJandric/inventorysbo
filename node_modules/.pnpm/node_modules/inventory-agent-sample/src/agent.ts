import { createAgent, hostedMcpTool } from '@openai/agents';

const inventoryTool = hostedMcpTool({
  label: 'inventory-supabase',
  url: 'https://<TON_MCP_PUBLIC_URL>/mcp', // TODO: replace with the deployed MCP server URL
  allowed_tools: [
    'items.search',
    'items.get',
    'items.similar',
    'items.update_status',
    'items.set_prices',
    'banking.classes.list',
    'banking.summary',
    'market.analyses.search',
    'market.analyses.get',
    'market.analyses.upsert',
    'realestate.listings.search',
    'trades.list',
    'trades.record',
    'trades.close',
    'exports.generate',
  ],
  timeout_ms: 120000,
});

export const agent = createAgent({
  model: 'gpt-4.1-mini',
  system: 'Assistant portefeuille. N\'invente pas de chiffres: utilise les outils.',
  tools: [inventoryTool],
});

// Simple demo runner
async function demo() {
  console.log('Running agent demo...');
  // Example: chain items.search -> exports.generate
  // Note: Replace below with actual Agents SDK invocation when available
  console.log('Pretend calling items.search then exports.generate via hosted tool.');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  demo().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}


