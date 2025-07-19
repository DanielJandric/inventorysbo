# Exemple de configuration locale
# Copiez ce fichier en config.py et remplacez par vos vraies clés
import os

# Supabase
os.environ['SUPABASE_URL'] = "https://votre-projet.supabase.co"
os.environ['SUPABASE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.votre_clé_supabase_ici"

# APIs
os.environ['EODHD_API_KEY'] = "votre_clé_eodhd_ici"
os.environ['OPENAI_API_KEY'] = "sk-votre_clé_openai_ici"

print("✅ Variables d'environnement configurées")
print("⚠️  N'oubliez pas de remplacer les valeurs par vos vraies clés !") 