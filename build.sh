#!/usr/bin/env bash
set -o errexit

echo "🚀 Build Render - BONVIN Collection"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build terminé!"
echo "Variables d'environnement:"
echo "- SUPABASE_URL: ${SUPABASE_URL:+✅ Définie}"
echo "- SUPABASE_KEY: ${SUPABASE_KEY:+✅ Définie}"  
echo "- OPENAI_API_KEY: ${OPENAI_API_KEY:+✅ Définie}"
