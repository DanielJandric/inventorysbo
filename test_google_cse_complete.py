#!/usr/bin/env python3
"""
Test complet de l'intégration Google CSE
"""

import requests
import json
from google_cse_integration import GoogleCSEIntegration

def test_google_cse_integration():
    """Test complet de l'intégration Google CSE"""
    print("🧪 Test Complet Google CSE Integration")
    print("=" * 50)
    
    # Initialiser l'intégration
    cse = GoogleCSEIntegration()
    status = cse.get_status()
    
    print(f"🔍 Engine ID: {status['engine_id']}")
    print(f"🔑 API Key: {'✅ Configurée' if status['api_key_configured'] else '❌ Manquante'}")
    print(f"📊 Status: {status['status']}")
    
    if not status['api_key_configured']:
        print("❌ Clé API manquante")
        return
    
    # Test 1: Recherche générale
    print("\n🔍 Test 1: Recherche générale")
    response = cse.search("AAPL stock price", num_results=3)
    if response:
        print(f"✅ Recherche réussie! {response.total_results} résultats")
        for i, result in enumerate(response.results[:2], 1):
            print(f"   {i}. {result.title}")
    else:
        print("❌ Échec de la recherche générale")
    
    # Test 2: Recherche de prix d'action
    print("\n💰 Test 2: Recherche de prix d'action")
    price_data = cse.search_stock_price("AAPL")
    if price_data:
        print(f"✅ Prix trouvé: {price_data['price']} {price_data['currency']}")
        print(f"   Source: {price_data['source']}")
    else:
        print("❌ Prix non trouvé")
    
    # Test 3: Recherche de nouvelles du marché
    print("\n📰 Test 3: Recherche de nouvelles du marché")
    news = cse.search_market_news(['stock market', 'financial news'])
    if news:
        print(f"✅ {len(news)} articles trouvés")
        for i, article in enumerate(news[:2], 1):
            print(f"   {i}. {article['title']}")
    else:
        print("❌ Aucune nouvelle trouvée")
    
    # Test 4: Recherche de briefing du marché
    print("\n📊 Test 4: Recherche de briefing du marché")
    briefing = cse.search_market_briefing("global")
    if briefing:
        print(f"✅ Briefing trouvé ({len(briefing['sources'])} sources)")
        print(f"   Contenu: {briefing['content'][:100]}...")
    else:
        print("❌ Briefing non trouvé")
    
    print("\n🎉 Tests terminés!")

def test_web_interface():
    """Test de l'interface web"""
    print("\n🌐 Test de l'interface web")
    print("=" * 30)
    
    try:
        # Test du statut
        response = requests.get("http://localhost:5000/api/google-cse/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Interface web accessible")
            print(f"   Status: {data.get('status', 'N/A')}")
        else:
            print(f"❌ Erreur interface web: {response.status_code}")
    except Exception as e:
        print(f"❌ Impossible d'accéder à l'interface web: {e}")

if __name__ == "__main__":
    test_google_cse_integration()
    test_web_interface() 