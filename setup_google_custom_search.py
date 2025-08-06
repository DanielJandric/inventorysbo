#!/usr/bin/env python3
"""
Script de configuration pour Google Custom Search Engine
Configure automatiquement les nouvelles variables d'environnement
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

def update_env_file(engine_id: str, api_key: str):
    """Met à jour le fichier .env avec les nouvelles variables"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ Fichier .env non trouvé")
        return False
    
    try:
        # Lire le contenu actuel
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Remplacer les variables
        content = content.replace(
            'GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_google_custom_search_engine_id_here',
            f'GOOGLE_CUSTOM_SEARCH_ENGINE_ID={engine_id}'
        )
        content = content.replace(
            'GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_custom_search_api_key_here',
            f'GOOGLE_CUSTOM_SEARCH_API_KEY={api_key}'
        )
        
        # Écrire le nouveau contenu
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✅ Fichier .env mis à jour avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour fichier .env: {e}")
        return False

def test_google_custom_search(engine_id: str, api_key: str):
    """Test de l'API Google Custom Search"""
    print("🧪 Test de l'API Google Custom Search")
    print("=" * 50)
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': engine_id,
        'q': 'AAPL stock price',
        'num': 3
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Google Custom Search fonctionnelle!")
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

def update_google_cse_integration():
    """Met à jour l'intégration Google CSE pour utiliser les nouvelles variables"""
    print("\n🔧 Mise à jour de l'intégration Google CSE...")
    
    try:
        # Lire le fichier d'intégration
        with open('google_cse_integration.py', 'r') as f:
            content = f.read()
        
        # Remplacer les variables d'environnement
        content = content.replace(
            "self.api_key = os.getenv('GOOGLE_SEARCH_API_KEY')",
            "self.api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')"
        )
        content = content.replace(
            'self.engine_id = "0426c6b27374b4a72"  # Votre Search Engine ID',
            'self.engine_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID", "0426c6b27374b4a72")'
        )
        
        # Écrire le fichier mis à jour
        with open('google_cse_integration.py', 'w') as f:
            f.write(content)
        
        print("✅ Intégration Google CSE mise à jour")
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour intégration: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Configuration Google Custom Search Engine")
    print("=" * 60)
    
    # Demander les informations à l'utilisateur
    print("\n📝 Veuillez fournir vos informations Google Custom Search Engine:")
    
    engine_id = input("🔍 Engine ID: ").strip()
    api_key = input("🔑 API Key: ").strip()
    
    if not engine_id or not api_key:
        print("❌ Engine ID et API Key sont requis")
        return
    
    print(f"\n🔍 Engine ID: {engine_id}")
    print(f"🔑 API Key: {'*' * (len(api_key) - 8) + api_key[-8:] if len(api_key) > 8 else '***'}")
    
    # Confirmer
    confirm = input("\n✅ Confirmer la configuration? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Configuration annulée")
        return
    
    # Mettre à jour le fichier .env
    print("\n📝 Mise à jour du fichier .env...")
    if update_env_file(engine_id, api_key):
        # Tester l'API
        print("\n🧪 Test de l'API...")
        if test_google_custom_search(engine_id, api_key):
            # Mettre à jour l'intégration
            if update_google_cse_integration():
                print("\n🎉 Configuration réussie!")
                print("✅ Google Custom Search Engine configuré et testé")
                print("✅ Intégration mise à jour")
                print("\n📝 Prochaines étapes:")
                print("   1. Testez avec: python google_cse_integration.py")
                print("   2. Démarrez l'app: python app.py")
                print("   3. Accédez à: http://localhost:5000/google-cse")
            else:
                print("⚠️ Configuration partielle - intégration non mise à jour")
        else:
            print("❌ Échec du test API - vérifiez vos clés")
    else:
        print("❌ Échec de la mise à jour du fichier .env")

if __name__ == "__main__":
    main() 