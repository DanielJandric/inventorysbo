#!/usr/bin/env python3
"""
Script pour créer le fichier .env avec la configuration Google CSE
"""

def create_env_file():
    """Crée le fichier .env avec la configuration correcte"""
    env_content = """# Configuration OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Configuration Google Custom Search Engine
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=0426c6b27374b4a72
GOOGLE_CUSTOM_SEARCH_API_KEY=AIzaSyCX-eoWQ8RCq0_TP5KNf29y5m4pJ7X7HtA

# Configuration Google Search API (Legacy)
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=0426c6b27374b4a72

# Configuration Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Configuration FreeCurrency
FREECURRENCY_API_KEY=your_frecurrency_api_key_here

# Configuration Email (Gmail)
GMAIL_USER=your_gmail_user_here
GMAIL_PASSWORD=your_gmail_password_here

# Configuration Application
FLASK_BASE_URL=http://localhost:5000
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Fichier .env créé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur création fichier .env: {e}")
        return False

if __name__ == "__main__":
    create_env_file() 