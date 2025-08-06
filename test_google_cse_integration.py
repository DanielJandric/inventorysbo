#!/usr/bin/env python3
"""
Test complet de l'intégration Google CSE
Teste toutes les fonctionnalités de l'intégration
"""

import requests
import json
import time
from typing import Dict, Any

class GoogleCSETester:
    """Classe de test pour l'intégration Google CSE"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
    
    def test_status_endpoint(self) -> bool:
        """Test du endpoint de statut"""
        print("🔍 Test du endpoint de statut...")
        
        try:
            response = requests.get(f"{self.base_url}/api/google-cse/status")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {data.get('status', 'unknown')}")
                print(f"🔍 Engine ID: {data.get('engine_id', 'N/A')}")
                print(f"🔑 API Key: {'✅ Configurée' if data.get('api_key_configured') else '❌ Manquante'}")
                return True
            else:
                print(f"❌ Erreur: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_search_endpoint(self, query: str = "AAPL stock price") -> bool:
        """Test du endpoint de recherche"""
        print(f"\n🔍 Test de recherche: '{query}'")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/google-cse/search",
                json={"query": query},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Recherche réussie!")
                    print(f"📊 Résultats trouvés: {data.get('total_results', 0)}")
                    print(f"⏱️ Temps de recherche: {data.get('search_time', 0)}s")
                    
                    results = data.get('results', [])
                    if results:
                        print(f"📰 Premier résultat: {results[0].get('title', 'N/A')}")
                    
                    return True
                else:
                    print(f"❌ Échec de recherche: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_stock_price_endpoint(self, symbol: str = "AAPL") -> bool:
        """Test du endpoint de prix d'action"""
        print(f"\n💰 Test de prix d'action: {symbol}")
        
        try:
            response = requests.get(f"{self.base_url}/api/google-cse/stock-price/{symbol}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    price_data = data.get('data', {})
                    print(f"✅ Prix trouvé: {price_data.get('price', 'N/A')} {price_data.get('currency', 'USD')}")
                    print(f"📊 Source: {price_data.get('source', 'N/A')}")
                    print(f"🎯 Confiance: {price_data.get('confidence', 0) * 100:.1f}%")
                    return True
                else:
                    print(f"❌ Aucun prix trouvé: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_market_news_endpoint(self) -> bool:
        """Test du endpoint de nouvelles du marché"""
        print(f"\n📰 Test de nouvelles du marché")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/google-cse/market-news",
                json={"keywords": ["stock market", "financial news"]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    news = data.get('news', [])
                    print(f"✅ Nouvelles trouvées: {len(news)}")
                    
                    if news:
                        print(f"📰 Premier article: {news[0].get('title', 'N/A')}")
                    
                    return True
                else:
                    print(f"❌ Aucune nouvelle trouvée: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_market_briefing_endpoint(self) -> bool:
        """Test du endpoint de briefing du marché"""
        print(f"\n📊 Test de briefing du marché")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/google-cse/market-briefing",
                json={"location": "global"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    briefing = data.get('briefing', {})
                    print(f"✅ Briefing trouvé!")
                    print(f"📍 Localisation: {briefing.get('location', 'N/A')}")
                    print(f"📝 Contenu: {len(briefing.get('content', ''))} caractères")
                    print(f"🔗 Sources: {len(briefing.get('sources', []))}")
                    return True
                else:
                    print(f"❌ Aucun briefing trouvé: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_web_interface(self) -> bool:
        """Test de l'interface web"""
        print(f"\n🌐 Test de l'interface web")
        
        try:
            response = requests.get(f"{self.base_url}/google-cse")
            
            if response.status_code == 200:
                print("✅ Interface web accessible")
                return True
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests"""
        print("🧪 Test complet de l'intégration Google CSE")
        print("=" * 60)
        
        tests = [
            ("Status Endpoint", self.test_status_endpoint),
            ("Search Endpoint", lambda: self.test_search_endpoint("AAPL stock price")),
            ("Stock Price Endpoint", lambda: self.test_stock_price_endpoint("AAPL")),
            ("Market News Endpoint", self.test_market_news_endpoint),
            ("Market Briefing Endpoint", self.test_market_briefing_endpoint),
            ("Web Interface", self.test_web_interface),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                success = test_func()
                results[test_name] = success
                print(f"{'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
            except Exception as e:
                print(f"❌ ERREUR: {e}")
                results[test_name] = False
        
        # Résumé
        print(f"\n{'='*60}")
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASSÉ" if success else "❌ ÉCHOUÉ"
            print(f"{test_name}: {status}")
        
        print(f"\n🎯 Résultat global: {passed}/{total} tests passés")
        
        if passed == total:
            print("🎉 Tous les tests sont passés! L'intégration Google CSE fonctionne parfaitement.")
        elif passed > total // 2:
            print("⚠️ La plupart des tests sont passés. Vérifiez la configuration.")
        else:
            print("❌ Plusieurs tests ont échoué. Vérifiez la configuration et les logs.")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": passed / total if total > 0 else 0,
            "results": results
        }

def main():
    """Fonction principale"""
    tester = GoogleCSETester()
    results = tester.run_all_tests()
    
    # Sauvegarder les résultats
    with open("google_cse_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Résultats sauvegardés dans: google_cse_test_results.json")

if __name__ == "__main__":
    main() 