#!/usr/bin/env bash
# start.sh - Script de démarrage pour Render

echo "🎯 Démarrage de l'application BONVIN..."

# Démarrer avec Gunicorn (gevent pour SSE/streaming)
exec gunicorn app:app \
  --worker-class gevent \
  --workers ${GUNICORN_WORKERS:-2} \
  --worker-connections ${GUNICORN_WORKER_CONNECTIONS:-1000} \
  --timeout ${GUNICORN_TIMEOUT:-120} \
  --graceful-timeout 30 \
  --keep-alive 65 \
  --preload \
  --bind 0.0.0.0:${PORT:-5000}
