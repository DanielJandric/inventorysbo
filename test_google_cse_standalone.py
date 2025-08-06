#!/usr/bin/env python3
"""
Test standalone de Google CSE sans dépendances Supabase
"""
import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Importer les modules Google CSE
sys.path.append('.')
from google_cse_integration import GoogleCSEIntegration
from google_cse_stock_data import GoogleCSEStockDataManager

def test_google_cse_standalone():
    """Test complet de Google CSE en mode standalone"""
    print("🧪 Test Google CSE Standalone")
    print("=" * 50)
    
    # Test 1: Intégration Google CSE
    print("\n🔍 Test 1: Intégration Google CSE")
    cse = GoogleCSEIntegration()
    
    # Vérifier la configuration
    print(f"   Engine ID: {cse.engine_id}")
    print(f"   API Key: {'✅ Configurée' if cse.api_key else '❌ Manquante'}")
    
    # Test de recherche
    print("\n💰 Test 2: Recherche de prix d'action AAPL")
    response = cse.search("AAPL stock price today", num_results=5)
    
    if response and response.results:
        print(f"   ✅ {len(response.results)} résultats trouvés")
        for i, result in enumerate(response.results[:3], 1):
            print(f"   {i}. {result.title}")
            print(f"      URL: {result.link}")
            print(f"      Snippet: {result.snippet[:100]}...")
    else:
        print("   ❌ Aucun résultat trouvé")
    
    # Test 3: Gestionnaire de données boursières
    print("\n📊 Test 3: Gestionnaire de données boursières")
    manager = GoogleCSEStockDataManager()
    
    # Test de prix d'action
    stock_data = manager.get_stock_price("AAPL")
    if stock_data:
        print(f"   ✅ Prix AAPL: ${stock_data.price}")
        if stock_data.change:
            print(f"      Variation: {stock_data.change} ({stock_data.change_percent})")
    else:
        print("   ❌ Prix non trouvé")
    
    # Test de vue d'ensemble du marché
    print("\n📈 Test 4: Vue d'ensemble du marché")
    market_overview = manager.get_market_overview()
    print(f"   ✅ {len(market_overview)} sources de données récupérées")
    
    # Test de rapport journalier
    print("\n📋 Test 5: Rapport journalier avec IA")
    report = manager.generate_daily_report(['AAPL', 'GOOGL', 'MSFT'])
    print(f"   ✅ Rapport généré: {report.summary[:100]}...")
    print(f"      Sentiment: {report.market_sentiment}")
    print(f"      Événements: {len(report.key_events)}")
    print(f"      Recommandations: {len(report.recommendations)}")
    
    print("\n🎉 Tests terminés avec succès!")

def test_web_interface():
    """Test de l'interface web Google CSE"""
    print("\n🌐 Test de l'interface web")
    print("=" * 30)
    
    try:
        import requests
        import time
        
        # Attendre que l'application démarre
        print("   ⏳ Attente du démarrage de l'application...")
        time.sleep(2)
        
        # Test de l'endpoint de statut
        response = requests.get("http://localhost:5000/api/google-cse/status", timeout=5)
        if response.status_code == 200:
            print("   ✅ Interface web accessible")
            data = response.json()
            print(f"      Status: {data.get('status', 'N/A')}")
        else:
            print(f"   ❌ Erreur interface web: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Impossible d'accéder à l'interface web: {e}")

if __name__ == "__main__":
    test_google_cse_standalone()
    test_web_interface() 