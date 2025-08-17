#!/usr/bin/env bash
# start.sh - Script de démarrage pour Render

echo "🎯 Démarrage de l'application BONVIN..."

# Démarrer avec Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT \
  --workers 1 \
  --timeout 120 \
  --graceful-timeout 120 \
  --keep-alive 75 \
  --preload \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  app:app
