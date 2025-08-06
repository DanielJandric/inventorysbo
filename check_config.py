#!/usr/bin/env python3
"""
Script de vérification rapide de la configuration
"""

import os
from dotenv import load_dotenv

def check_config():
    """Vérifie la configuration actuelle"""
    print("🔍 Vérification de la Configuration")
    print("=" * 50)
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Vérifier Google Search
    google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    google_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    print("🔍 Google Search API:")
    print(f"   🔑 API Key: {'✅ Configurée' if google_api_key and google_api_key != 'your_google_search_api_key_here' else '❌ Manquante'}")
    print(f"   🔍 Engine ID: {'✅ Configuré' if google_engine_id else '❌ Manquant'}")
    
    if google_engine_id:
        print(f"   📊 Votre Engine ID: {google_engine_id}")
    
    # Vérifier OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    print(f"\n🤖 OpenAI API: {'✅ Configurée' if openai_key and openai_key != 'your_openai_api_key_here' else '❌ Manquante'}")
    
    # Vérifier Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    print(f"🗄️ Supabase: {'✅ Configuré' if supabase_url and supabase_key else '❌ Manquant'}")
    
    # Résumé
    print("\n📊 Résumé:")
    google_ok = google_api_key and google_api_key != 'your_google_search_api_key_here' and google_engine_id
    openai_ok = openai_key and openai_key != 'your_openai_api_key_here'
    supabase_ok = supabase_url and supabase_key
    
    if google_ok:
        print("✅ Google Search API: Prêt à utiliser")
    else:
        print("❌ Google Search API: Configuration manquante")
        print("   📝 Suivez le guide: GET_GOOGLE_API_KEY.md")
    
    if openai_ok:
        print("✅ OpenAI API: Prêt à utiliser")
    else:
        print("❌ OpenAI API: Configuration manquante")
    
    if supabase_ok:
        print("✅ Supabase: Prêt à utiliser")
    else:
        print("❌ Supabase: Configuration manquante")
    
    # Recommandations
    print("\n💡 Recommandations:")
    if not google_ok:
        print("   1. Obtenez votre clé API Google (voir GET_GOOGLE_API_KEY.md)")
        print("   2. Testez avec: python test_google_search_quick.py")
    elif google_ok:
        print("   1. Testez Google Search: python test_google_search_quick.py")
        print("   2. Démarrez l'app: python app.py")
        print("   3. Accédez à: http://localhost:5000/unified-market")

if __name__ == "__main__":
    check_config() 