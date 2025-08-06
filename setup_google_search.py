#!/usr/bin/env python3
"""
Script de configuration pour Google Search API
Aide à configurer et tester l'API Google Search
"""

import os
import requests
from dotenv import load_dotenv

def check_google_search_config():
    """Vérifie la configuration Google Search"""
    print("🔍 Vérification de la configuration Google Search API")
    print("=" * 50)
    
    # Charger les variables d'environnement
    load_dotenv()
    
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    print(f"🔑 API Key: {'✅ Configurée' if api_key else '❌ Manquante'}")
    print(f"🔍 Search Engine ID: {'✅ Configuré' if engine_id else '❌ Manquant'}")
    
    if not api_key or not engine_id:
        print("\n⚠️ Configuration incomplète!")
        print("Veuillez configurer les variables d'environnement:")
        print("1. GOOGLE_SEARCH_API_KEY")
        print("2. GOOGLE_SEARCH_ENGINE_ID")
        return False
    
    return True

def test_google_search_api():
    """Test de l'API Google Search"""
    print("\n🧪 Test de l'API Google Search")
    print("=" * 30)
    
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not api_key or not engine_id:
        print("❌ Configuration manquante pour le test")
        return False
    
    # Test de recherche simple
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': engine_id,
        'q': 'AAPL stock price',
        'num': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Google Search fonctionnelle")
            print(f"📊 Résultats trouvés: {data.get('searchInformation', {}).get('totalResults', 0)}")
            return True
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"📝 Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_unified_market_manager():
    """Test du gestionnaire unifié avec Google Search"""
    print("\n🔗 Test du Gestionnaire Unifié")
    print("=" * 30)
    
    try:
        # Importer le gestionnaire unifié
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

def setup_instructions():
    """Affiche les instructions de configuration"""
    print("\n📋 Instructions de Configuration Google Search API")
    print("=" * 60)
    
    print("1. 🌐 Créer un projet Google Cloud:")
    print("   - Allez sur https://console.cloud.google.com/")
    print("   - Créez un nouveau projet")
    print("   - Activez l'API Custom Search Engine")
    
    print("\n2. 🔑 Créer une clé API:")
    print("   - Dans 'APIs & Services' > 'Credentials'")
    print("   - Cliquez sur 'Create Credentials' > 'API Key'")
    print("   - Copiez la clé API")
    
    print("\n3. 🔍 Créer un Custom Search Engine:")
    print("   - Allez sur https://programmablesearchengine.google.com/")
    print("   - Cliquez sur 'Create a search engine'")
    print("   - Laissez 'Sites to search' vide pour rechercher sur tout le web")
    print("   - Notez l'ID du moteur de recherche")
    
    print("\n4. ⚙️ Configurer les variables d'environnement:")
    print("   - Créez un fichier .env")
    print("   - Ajoutez:")
    print("     GOOGLE_SEARCH_API_KEY=votre_clé_api")
    print("     GOOGLE_SEARCH_ENGINE_ID=votre_id_moteur")
    
    print("\n5. 🧪 Tester la configuration:")
    print("   - Exécutez: python setup_google_search.py")
    print("   - Vérifiez que tous les tests passent")

def main():
    """Fonction principale"""
    print("🔧 Configuration Google Search API")
    print("=" * 50)
    
    # Vérifier la configuration
    config_ok = check_google_search_config()
    
    if config_ok:
        # Tester l'API
        api_ok = test_google_search_api()
        
        if api_ok:
            # Tester le gestionnaire unifié
            manager_ok = test_unified_market_manager()
            
            if manager_ok:
                print("\n🎉 Configuration Google Search API réussie!")
                print("✅ Tous les tests passent")
                print("🚀 Le gestionnaire unifié est opérationnel")
            else:
                print("\n⚠️ Problème avec le gestionnaire unifié")
        else:
            print("\n⚠️ Problème avec l'API Google Search")
    else:
        print("\n❌ Configuration manquante")
    
    # Afficher les instructions
    setup_instructions()

if __name__ == "__main__":
    main() 