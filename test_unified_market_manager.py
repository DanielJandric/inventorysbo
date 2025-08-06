#!/usr/bin/env python3
"""
Script de test pour le gestionnaire de marché unifié
Vérifie toutes les fonctionnalités du système centralisé
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:5000"
TEST_SYMBOLS = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]

class UnifiedMarketTester:
    """Classe de test pour le gestionnaire de marché unifié"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'UnifiedMarketTester/1.0'
        })
        self.results = {
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'start_time': datetime.now().isoformat()
            }
        }
    
    def log_test(self, test_name: str, success: bool, details: str = "", data: Dict = None):
        """Enregistre un résultat de test"""
        test_result = {
            'name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.results['tests'].append(test_result)
        
        if success:
            self.results['summary']['passed'] += 1
            print(f"✅ {test_name}: {details}")
        else:
            self.results['summary']['failed'] += 1
            print(f"❌ {test_name}: {details}")
        
        self.results['summary']['total'] += 1
    
    def test_status_endpoint(self):
        """Test du endpoint de statut"""
        try:
            response = self.session.get(f"{self.base_url}/api/unified/status")
            data = response.json()
            
            if response.status_code == 200 and 'status' in data:
                self.log_test(
                    "Statut du gestionnaire unifié",
                    True,
                    f"Statut: {data.get('status', 'unknown')}, Cache: {data.get('cache_size', 0)}"
                )
                return True
            else:
                self.log_test(
                    "Statut du gestionnaire unifié",
                    False,
                    f"Code: {response.status_code}, Réponse: {data}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Statut du gestionnaire unifié",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_stock_price_search(self, symbol: str):
        """Test de recherche de prix d'action"""
        try:
            response = self.session.get(f"{self.base_url}/api/unified/stock-price/{symbol}")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                stock_data = data['data']
                self.log_test(
                    f"Recherche prix {symbol}",
                    True,
                    f"Prix: {stock_data.get('price')} {stock_data.get('currency')}, Source: {stock_data.get('source')}",
                    stock_data
                )
                return True
            else:
                self.log_test(
                    f"Recherche prix {symbol}",
                    False,
                    f"Code: {response.status_code}, Erreur: {data.get('error', 'Unknown')}"
                )
                return False
        except Exception as e:
            self.log_test(
                f"Recherche prix {symbol}",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_market_briefing(self):
        """Test de génération de briefing de marché"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/unified/market-briefing",
                json={"location": "global"}
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                briefing = data['data']
                self.log_test(
                    "Briefing de marché",
                    True,
                    f"Source: {briefing.get('source')}, Contenu: {len(briefing.get('content', ''))} caractères",
                    briefing
                )
                return True
            else:
                self.log_test(
                    "Briefing de marché",
                    False,
                    f"Code: {response.status_code}, Erreur: {data.get('error', 'Unknown')}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Briefing de marché",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_daily_news(self):
        """Test de récupération des nouvelles quotidiennes"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/unified/daily-news",
                json={"categories": ["finance", "markets"]}
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                news_items = data['data']['news_items']
                self.log_test(
                    "Nouvelles quotidiennes",
                    True,
                    f"{len(news_items)} nouvelles récupérées",
                    {"count": len(news_items), "items": news_items[:2]}  # Limiter les données
                )
                return True
            else:
                self.log_test(
                    "Nouvelles quotidiennes",
                    False,
                    f"Code: {response.status_code}, Erreur: {data.get('error', 'Unknown')}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Nouvelles quotidiennes",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_market_alerts(self):
        """Test de récupération des alertes de marché"""
        try:
            response = self.session.get(f"{self.base_url}/api/unified/market-alerts")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                alerts = data['data']['alerts']
                self.log_test(
                    "Alertes de marché",
                    True,
                    f"{len(alerts)} alertes récupérées",
                    {"count": len(alerts), "alerts": alerts[:2]}  # Limiter les données
                )
                return True
            else:
                self.log_test(
                    "Alertes de marché",
                    False,
                    f"Code: {response.status_code}, Erreur: {data.get('error', 'Unknown')}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Alertes de marché",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_bulk_price_update(self):
        """Test de mise à jour en masse des prix"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/unified/update-all-prices",
                json={"symbols": TEST_SYMBOLS[:3]}  # Tester avec 3 symboles
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test(
                    "Mise à jour en masse",
                    True,
                    f"Total: {data.get('total', 0)}, Réussis: {data.get('success_count', 0)}, Échecs: {data.get('failure_count', 0)}",
                    data
                )
                return True
            else:
                self.log_test(
                    "Mise à jour en masse",
                    False,
                    f"Code: {response.status_code}, Erreur: {data.get('error', 'Unknown')}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Mise à jour en masse",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_cache_management(self):
        """Test de gestion du cache"""
        try:
            response = self.session.post(f"{self.base_url}/api/unified/clear-cache")
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                self.log_test(
                    "Gestion du cache",
                    True,
                    f"Cache vidé: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.log_test(
                    "Gestion du cache",
                    False,
                    f"Code: {response.status_code}, Erreur: {data.get('error', 'Unknown')}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Gestion du cache",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def test_web_interface(self):
        """Test de l'interface web"""
        try:
            response = self.session.get(f"{self.base_url}/unified-market")
            
            if response.status_code == 200:
                self.log_test(
                    "Interface web",
                    True,
                    f"Interface accessible, Taille: {len(response.content)} bytes"
                )
                return True
            else:
                self.log_test(
                    "Interface web",
                    False,
                    f"Code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Interface web",
                False,
                f"Erreur: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 Démarrage des tests du gestionnaire de marché unifié")
        print("=" * 60)
        
        # Test de base
        self.test_status_endpoint()
        time.sleep(1)
        
        # Tests de recherche de prix
        for symbol in TEST_SYMBOLS[:2]:  # Tester avec 2 symboles
            self.test_stock_price_search(symbol)
            time.sleep(1)
        
        # Tests de contenu de marché
        self.test_market_briefing()
        time.sleep(1)
        
        self.test_daily_news()
        time.sleep(1)
        
        self.test_market_alerts()
        time.sleep(1)
        
        # Tests de gestion
        self.test_bulk_price_update()
        time.sleep(1)
        
        self.test_cache_management()
        time.sleep(1)
        
        # Test d'interface
        self.test_web_interface()
        
        # Résumé
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Affiche le résumé des tests"""
        summary = self.results['summary']
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        print(f"Total: {summary['total']}")
        print(f"✅ Réussis: {summary['passed']}")
        print(f"❌ Échecs: {summary['failed']}")
        print(f"📈 Taux de réussite: {(summary['passed'] / summary['total'] * 100):.1f}%")
        print(f"⏱️  Durée: {datetime.fromisoformat(summary['start_time']).strftime('%H:%M:%S')}")
        
        if summary['failed'] > 0:
            print("\n🔍 Tests échoués:")
            for test in self.results['tests']:
                if not test['success']:
                    print(f"  - {test['name']}: {test['details']}")
    
    def save_results(self):
        """Sauvegarde les résultats dans un fichier"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_unified_market_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Résultats sauvegardés dans: {filename}")
        except Exception as e:
            print(f"\n⚠️ Erreur sauvegarde résultats: {e}")

def main():
    """Fonction principale"""
    print("🔗 Test du Gestionnaire de Marché Unifié")
    print("=" * 60)
    
    # Vérifier que l'application est en cours d'exécution
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ L'application Flask n'est pas accessible")
            print("   Assurez-vous que l'application est démarrée: python app.py")
            return
    except Exception as e:
        print("❌ Impossible de se connecter à l'application")
        print(f"   Erreur: {e}")
        print("   Assurez-vous que l'application est démarrée: python app.py")
        return
    
    print("✅ Application accessible, démarrage des tests...")
    
    # Créer et exécuter les tests
    tester = UnifiedMarketTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 