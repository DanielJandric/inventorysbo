#!/usr/bin/env python3
"""
Script de test pour l'intégration de la recherche web OpenAI
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_web_search_status():
    """Test du statut de la recherche web"""
    print("🧪 Test du statut de la recherche web")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:5000/api/web-search/status")
        if response.status_code == 200:
            status = response.json()
            print("✅ Statut récupéré avec succès")
            print(f"   Disponible: {status.get('available', False)}")
            print(f"   OpenAI configuré: {status.get('openai_configured', False)}")
            print(f"   Types de recherche: {status.get('search_types', [])}")
            print(f"   Durée cache: {status.get('cache_duration', 'N/A')} secondes")
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def test_market_briefing_web_search():
    """Test de génération de briefing avec recherche web"""
    print("\n🧪 Test de génération de briefing avec recherche web")
    print("=" * 50)
    
    try:
        data = {
            "user_location": {
                "country": "CH",
                "city": "Genève",
                "region": "Genève"
            },
            "search_context_size": "high"
        }
        
        response = requests.post(
            "http://localhost:5000/api/web-search/market-briefing",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Briefing généré avec succès")
            print(f"   Source: {result.get('source', 'N/A')}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            print(f"   Longueur contenu: {len(result.get('briefing', ''))} caractères")
            
            # Afficher un extrait du contenu
            content = result.get('briefing', '')
            if content:
                print(f"\n📝 Extrait du briefing:")
                print("-" * 30)
                print(content[:300] + "..." if len(content) > 300 else content)
                print("-" * 30)
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def test_financial_markets_search():
    """Test de recherche de données de marché"""
    print("\n🧪 Test de recherche de données de marché")
    print("=" * 50)
    
    try:
        data = {
            "search_type": "market_data",
            "user_location": {
                "country": "CH",
                "city": "Genève"
            },
            "search_context_size": "medium"
        }
        
        response = requests.post(
            "http://localhost:5000/api/web-search/financial-markets",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Recherche de marché réussie")
            print(f"   Type: {result.get('result', {}).get('search_type', 'N/A')}")
            print(f"   Citations: {len(result.get('result', {}).get('citations', []))}")
            print(f"   Domaines recherchés: {result.get('result', {}).get('domains_searched', [])}")
            
            # Afficher un extrait du contenu
            content = result.get('result', {}).get('content', '')
            if content:
                print(f"\n📊 Extrait des données de marché:")
                print("-" * 30)
                print(content[:300] + "..." if len(content) > 300 else content)
                print("-" * 30)
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def test_stock_search():
    """Test de recherche d'information sur une action"""
    print("\n🧪 Test de recherche d'information sur une action")
    print("=" * 50)
    
    try:
        symbol = "AAPL"
        response = requests.get(
            f"http://localhost:5000/api/web-search/stock/{symbol}",
            params={
                "location": json.dumps({
                    "country": "US",
                    "city": "New York"
                })
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Recherche pour {symbol} réussie")
            print(f"   Citations: {len(result.get('result', {}).get('citations', []))}")
            print(f"   Type: {result.get('result', {}).get('search_type', 'N/A')}")
            
            # Afficher un extrait du contenu
            content = result.get('result', {}).get('content', '')
            if content:
                print(f"\n📈 Extrait des informations sur {symbol}:")
                print("-" * 30)
                print(content[:300] + "..." if len(content) > 300 else content)
                print("-" * 30)
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def test_market_alerts():
    """Test de recherche d'alertes de marché"""
    print("\n🧪 Test de recherche d'alertes de marché")
    print("=" * 50)
    
    try:
        response = requests.get(
            "http://localhost:5000/api/web-search/market-alerts",
            params={"type": "breaking_news"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Alertes de marché récupérées")
            print(f"   Type d'alerte: {result.get('alert_type', 'N/A')}")
            print(f"   Citations: {len(result.get('result', {}).get('citations', []))}")
            
            # Afficher un extrait du contenu
            content = result.get('result', {}).get('content', '')
            if content:
                print(f"\n🚨 Extrait des alertes:")
                print("-" * 30)
                print(content[:300] + "..." if len(content) > 300 else content)
                print("-" * 30)
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def test_integration_with_existing_endpoints():
    """Test d'intégration avec les endpoints existants"""
    print("\n🧪 Test d'intégration avec les endpoints existants")
    print("=" * 50)
    
    try:
        # Test du trigger de marché avec web search
        response = requests.post("http://localhost:5000/api/market-updates/trigger")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Trigger de marché avec web search réussi")
            print(f"   Source: {result.get('update', {}).get('source', 'N/A')}")
            print(f"   Type: {result.get('update', {}).get('trigger_type', 'N/A')}")
        else:
            print(f"❌ Erreur trigger: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 Test de l'intégration Web Search OpenAI")
    print("=" * 60)
    print(f"⏰ Début des tests: {datetime.now().strftime('%H:%M:%S')}")
    
    # Tests séquentiels
    test_web_search_status()
    test_market_briefing_web_search()
    test_financial_markets_search()
    test_stock_search()
    test_market_alerts()
    test_integration_with_existing_endpoints()
    
    print(f"\n🏁 Tests terminés: {datetime.now().strftime('%H:%M:%S')}")
    print("\n💡 Vérifiez que:")
    print("   ✅ Le serveur Flask est démarré sur localhost:5000")
    print("   ✅ La clé API OpenAI est configurée")
    print("   ✅ Les imports du module web_search_manager fonctionnent")
    print("   ✅ Les nouvelles routes sont accessibles")

if __name__ == "__main__":
    main() 