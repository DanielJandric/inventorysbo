# Installation & Configuration

## Prérequis
- Python 3.11+
- Node/npm (pour Puppeteer, optionnel en local; en prod Render géré par `build.sh` si npm dispo)
- Compte Supabase (URL + clé anon)

## Installation locale
```bash
git clone https://github.com/DanielJandric/inventorysbo.git
cd inventorysbo
python -m venv venv
# Windows
venv\\Scripts\\activate
# macOS/Linux
# source venv/bin/activate
pip install -r requirements.txt
```

## Variables d'environnement (.env)
```
SUPABASE_URL=...
SUPABASE_KEY=...
OPENAI_API_KEY=...
# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=...
EMAIL_PASSWORD=...
EMAIL_RECIPIENTS=a@ex.com,b@ex.com
# Worker
MARKET_BRIEF_TIME=21:30
MARKET_BRIEF_REGION=US
STOCK_REFRESH_TIMES=09:00,11:00,13:00,15:00,17:00,21:30
# Redis (optionnel)
REDIS_URL=redis://...
```

## Démarrer
- Dev: `python app.py` → http://localhost:5000
- Worker (optionnel): `python background_worker.py`

## Production (Render)
- `build.sh` installe Python deps et tente `npm ci` (si npm présent)
- `start.sh` lance Gunicorn: `app:app`








