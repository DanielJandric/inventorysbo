# Background Worker

## Rôles
- Briefing de marché (Seeking Alpha): nightly
- Rafraîchissement des prix d'actions: créneaux configurables

## Tâches
- `run_nightly_market_brief()`
- `run_stock_prices_refresh_schedule()`

## Configuration (env)
- `MARKET_BRIEF_TIME` (ex: `21:30`)
- `MARKET_BRIEF_REGION` (ex: `US`)
- `STOCK_REFRESH_TIMES` (CSV, ex: `09:00,11:00,13:00,...`)
- `REDIS_URL` (optionnel, cache pour Seeking Alpha)
- Email (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASSWORD`, `EMAIL_RECIPIENTS`)

## Lancement
- `python background_worker.py`





