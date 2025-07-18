#!/usr/bin/env bash
set -o errexit

echo "🎯 Démarrage de l'application BONVIN..."

# On lance Gunicorn en lui indiquant de chercher la variable 'app' dans le fichier 'app.py'
exec gunicorn --bind 0.0.0.0:$PORT app:app
