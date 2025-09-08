#!/usr/bin/env bash
# start.sh - Script de démarrage pour Render

echo "🎯 Démarrage de l'application BONVIN..."

# Démarrer avec Gunicorn (I/O friendly)
exec gunicorn app:app \
  --worker-class gthread \
  --threads ${GUNICORN_THREADS:-8} \
  --workers ${GUNICORN_WORKERS:-2} \
  --timeout ${GUNICORN_TIMEOUT:-120} \
  --keep-alive 2 \
  --bind 0.0.0.0:${PORT:-5000}
