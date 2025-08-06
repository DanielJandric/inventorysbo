#!/usr/bin/env python3
"""
Test rapide de la clé API Google CSE fournie par l'utilisateur
"""

import os
import requests
from dotenv import load_dotenv

def test_google_cse_api():
    """Test de l'API Google CSE avec la clé fournie"""
    print("🧪 Test de la clé API Google CSE")
    print("=" * 50)
    
    # Configuration
    api_key = "AIzaSyCX-eoWQ8RCq0_TP5KNf29y5m4pJ7X7HtA"
    engine_id = "0426c6b27374b4a72"
    
    print(f"🔍 Engine ID: {engine_id}")
    print(f"🔑 API Key: {api_key[:20]}...{api_key[-8:]}")
    
    # Test de l'API
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': engine_id,
        'q': 'AAPL stock price',
        'num': 3
    }
    
    try:
        print("\n🔍 Test de recherche...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Google CSE fonctionnelle!")
            print(f"📊 Résultats trouvés: {data.get('searchInformation', {}).get('totalResults', 0)}")
            
            items = data.get('items', [])
            if items:
                print("\n📰 Premiers résultats:")
                for i, item in enumerate(items[:3], 1):
                    print(f"{i}. {item.get('title', 'Sans titre')}")
                    print(f"   URL: {item.get('link', 'N/A')}")
                    print(f"   Snippet: {item.get('snippet', 'N/A')[:100]}...")
                    print()
            
            return True
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"📝 Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def update_env_file():
    """Met à jour le fichier .env avec la nouvelle clé"""
    print("\n📝 Mise à jour du fichier .env...")
    
    try:
        # Lire le contenu actuel
        with open('.env', 'r') as f:
            content = f.read()
        
        # Remplacer les variables
        content = content.replace(
            'GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_google_custom_search_engine_id_here',
            'GOOGLE_CUSTOM_SEARCH_ENGINE_ID=0426c6b27374b4a72'
        )
        content = content.replace(
            'GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_custom_search_api_key_here',
            'GOOGLE_CUSTOM_SEARCH_API_KEY=AIzaSyCX-eoWQ8RCq0_TP5KNf29y5m4pJ7X7HtA'
        )
        
        # Écrire le nouveau contenu
        with open('.env', 'w') as f:
            f.write(content)
        
        print("✅ Fichier .env mis à jour avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour fichier .env: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Configuration Google CSE avec votre clé API")
    print("=" * 60)
    
    # Test de l'API
    if test_google_cse_api():
        # Mettre à jour le fichier .env
        if update_env_file():
            print("\n🎉 Configuration réussie!")
            print("✅ Google CSE configuré et testé")
            print("\n📝 Prochaines étapes:")
            print("   1. Testez avec: python google_cse_integration.py")
            print("   2. Démarrez l'app: python app.py")
            print("   3. Accédez à: http://localhost:5000/google-cse")
        else:
            print("❌ Échec de la mise à jour du fichier .env")
    else:
        print("❌ Échec du test API - vérifiez votre clé")

if __name__ == "__main__":
    main() 