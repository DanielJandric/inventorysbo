#!/usr/bin/env python3
"""
Script de configuration des variables d'environnement
Configure automatiquement les variables pour Google Search API
"""

import os
from pathlib import Path

def create_env_file():
    """Crée le fichier .env avec les configurations"""
    env_content = """# Configuration Google Search API
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=0426c6b27374b4a72

# Configuration OpenAI
OPENAI_API_KEY=your_openai_api_key_here

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
    
    env_path = Path('.env')
    
    if env_path.exists():
        print("⚠️ Le fichier .env existe déjà")
        print("📝 Contenu actuel:")
        with open(env_path, 'r') as f:
            print(f.read())
        
        response = input("\nVoulez-vous le remplacer? (y/n): ")
        if response.lower() != 'y':
            print("❌ Configuration annulée")
            return False
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ Fichier .env créé avec succès")
        print(f"🔍 Search Engine ID configuré: 0426c6b27374b4a72")
        return True
    except Exception as e:
        print(f"❌ Erreur création fichier .env: {e}")
        return False

def check_current_config():
    """Vérifie la configuration actuelle"""
    print("🔍 Vérification de la configuration actuelle")
    print("=" * 50)
    
    # Vérifier les variables d'environnement
    google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    google_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    print(f"🔑 GOOGLE_SEARCH_API_KEY: {'✅ Configurée' if google_api_key else '❌ Manquante'}")
    print(f"🔍 GOOGLE_SEARCH_ENGINE_ID: {'✅ Configuré' if google_engine_id else '❌ Manquant'}")
    
    if google_engine_id:
        print(f"📊 ID du moteur: {google_engine_id}")
    
    return google_api_key and google_engine_id

def setup_instructions():
    """Affiche les instructions de configuration"""
    print("\n📋 Instructions de Configuration")
    print("=" * 40)
    
    print("1. 🔑 Obtenir la clé API Google:")
    print("   - Allez sur https://console.cloud.google.com/")
    print("   - Créez un projet ou sélectionnez un existant")
    print("   - Activez l'API Custom Search Engine")
    print("   - Créez une clé API dans 'Credentials'")
    
    print("\n2. ⚙️ Configurer les variables:")
    print("   - Ouvrez le fichier .env")
    print("   - Remplacez 'your_google_search_api_key_here' par votre clé API")
    print("   - Le Search Engine ID est déjà configuré: 0426c6b27374b4a72")
    
    print("\n3. 🧪 Tester la configuration:")
    print("   - Exécutez: python setup_google_search.py")
    print("   - Vérifiez que tous les tests passent")

def main():
    """Fonction principale"""
    print("🔧 Configuration Google Search API")
    print("=" * 50)
    
    # Vérifier la configuration actuelle
    config_ok = check_current_config()
    
    if not config_ok:
        print("\n📝 Création du fichier .env...")
        if create_env_file():
            print("\n✅ Configuration initiale terminée")
            print("📝 Veuillez maintenant:")
            print("   1. Obtenir votre clé API Google")
            print("   2. Modifier le fichier .env avec votre clé")
            print("   3. Tester avec: python setup_google_search.py")
        else:
            print("❌ Échec de la configuration")
    else:
        print("\n✅ Configuration déjà présente")
        print("🧪 Vous pouvez tester avec: python setup_google_search.py")
    
    # Afficher les instructions
    setup_instructions()

if __name__ == "__main__":
    main() 