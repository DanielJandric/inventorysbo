#!/usr/bin/env python3
"""
Test rapide pour Google Search API avec votre Search Engine ID
"""

import os
import requests
from dotenv import load_dotenv

def test_google_search_with_user_id():
    """Test avec votre Search Engine ID"""
    print("🧪 Test Google Search API avec votre Search Engine ID")
    print("=" * 60)
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Votre Search Engine ID
    engine_id = "0426c6b27374b4a72"
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    
    print(f"🔍 Search Engine ID: {engine_id}")
    print(f"🔑 API Key: {'✅ Configurée' if api_key else '❌ Manquante'}")
    
    if not api_key:
        print("\n⚠️ Clé API manquante!")
        print("Veuillez configurer GOOGLE_SEARCH_API_KEY dans votre fichier .env")
        return False
    
    # Test de recherche
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': engine_id,
        'q': 'AAPL stock price today',
        'num': 3,
        'dateRestrict': 'd1'  # Recherche dans les dernières 24h
    }
    
    try:
        print("\n🔍 Test de recherche...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Google Search fonctionnelle!")
            print(f"📊 Résultats trouvés: {data.get('searchInformation', {}).get('totalResults', 0)}")
            
            # Afficher les premiers résultats
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

def test_unified_manager_with_user_id():
    """Test du gestionnaire unifié avec votre Search Engine ID"""
    print("\n🔗 Test du Gestionnaire Unifié")
    print("=" * 30)
    
    try:
        from unified_market_manager import create_unified_market_manager
        
        manager = create_unified_market_manager()
        status = manager.get_status()
        
        print(f"✅ Gestionnaire unifié: {status.get('status', 'unknown')}")
        print(f"📊 Sources disponibles: {', '.join(status.get('sources', []))}")
        
        # Test de recherche de prix
        print("\n🔍 Test de recherche de prix...")
        price_data = manager.get_stock_price("AAPL")
        
        if price_data:
            print(f"✅ Prix trouvé: {price_data.price} {price_data.currency}")
            print(f"📊 Source: {price_data.source}")
            print(f"🎯 Confiance: {price_data.confidence_score * 100:.1f}%")
        else:
            print("❌ Aucun prix trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur gestionnaire unifié: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Test Google Search API - Configuration Rapide")
    print("=" * 60)
    
    # Test de l'API Google Search
    api_ok = test_google_search_with_user_id()
    
    if api_ok:
        # Test du gestionnaire unifié
        manager_ok = test_unified_manager_with_user_id()
        
        if manager_ok:
            print("\n🎉 Configuration réussie!")
            print("✅ Votre Search Engine ID fonctionne parfaitement")
            print("🚀 Le gestionnaire unifié est opérationnel")
            print("\n📝 Prochaines étapes:")
            print("   1. Démarrez l'application: python app.py")
            print("   2. Accédez à: http://localhost:5000/unified-market")
            print("   3. Testez les fonctionnalités de recherche")
        else:
            print("\n⚠️ Problème avec le gestionnaire unifié")
    else:
        print("\n❌ Problème avec l'API Google Search")
        print("📝 Vérifiez votre clé API dans le fichier .env")

if __name__ == "__main__":
    main() 