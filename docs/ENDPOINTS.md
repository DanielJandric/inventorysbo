# Endpoints

## Pages
- GET `/` – Dashboard
- GET `/settings` – Paramètres & actions
- GET `/markets` – Mises à jour marchés

## Stocks
- GET `/api/stock-price/status`
- POST `/api/stock-price/update-all`
- POST `/api/stock-price/reset-requests`
- GET `/api/stock-price/cache/status`
- GET `/api/stock-price/history/{symbol}`

## Rapports PDF
- GET `/api/portfolio/pdf`
- GET `/api/reports/asset-class/{name}`
- GET `/api/reports/all-asset-classes`
- GET `/api/reports/bank/full` (params: `engine=weasyprint|puppeteer`, `scale`, `margin`, `format`, `landscape`)

## Market updates
- GET `/api/market-updates`
- POST `/api/market-updates/trigger`
- GET `/api/market-updates/scheduler-status`

## Email
- POST `/api/test-email`
- POST `/api/send-market-report-email`

## Divers
- GET `/api/endpoints`
- GET `/health`




