#!/usr/bin/env bash
# start.sh - Script de démarrage pour Render

echo "🎯 Démarrage de l'application BONVIN..."

# Démarrer avec Gunicorn (gthread - A/B test sans gevent)
exec gunicorn app:app \
  --worker-class gthread \
  --threads ${GUNICORN_THREADS:-8} \
  --workers ${GUNICORN_WORKERS:-2} \
  --timeout ${GUNICORN_TIMEOUT:-300} \
  --graceful-timeout 30 \
  --keep-alive 65 \
  --bind 0.0.0.0:${PORT:-5000}
