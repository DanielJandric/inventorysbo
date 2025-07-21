# Template de configuration - Remplacez par vos vraies valeurs
import os

# Supabase
os.environ['SUPABASE_URL'] = "https://votre-projet.supabase.co"
os.environ['SUPABASE_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.votre_clé_supabase_ici"

# APIs
os.environ['EODHD_API_KEY'] = "votre_clé_eodhd_ici"
os.environ['OPENAI_API_KEY'] = "sk-votre_clé_openai_ici"
os.environ['GEMINI_API_KEY'] = "votre_clé_gemini_ici"

print("✅ Variables d'environnement configurées")
print("⚠️  N'oubliez pas de remplacer les valeurs par vos vraies clés !")
print("📝 Exemple de format :")
print("   SUPABASE_URL = 'https://abc123.supabase.co'")
print("   SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123...'")
print("   EODHD_API_KEY = 'abc123def456'")
print("   OPENAI_API_KEY = 'sk-abc123def456...'")
print("   GEMINI_API_KEY = 'AIzaSyABC123DEF456...'") 