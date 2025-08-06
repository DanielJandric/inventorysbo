#!/usr/bin/env python3
"""
Script de test pour l'intégration Google Search API
Teste toutes les fonctionnalités de l'API Google Search
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/google-search"

def print_section(title):
    """Affiche une section de test"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_result(success, message, data=None):
    """Affiche le résultat d'un test"""
    status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
    print(f"{status}: {message}")
    if data and success:
        print(f"📊 Données: {json.dumps(data, indent=2, ensure_ascii=False)}")
    print()

def test_api_status():
    """Teste le statut de l'API Google Search"""
    print_section("Test du statut de l'API")
    
    try:
        response = requests.get(f"{API_BASE}/status", timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            print_result(True, "Statut de l'API récupéré avec succès", data)
            return data.get('available', False)
        else:
            print_result(False, f"Erreur HTTP {response.status_code}: {data.get('error', 'Erreur inconnue')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result(False, f"Erreur de connexion: {e}")
        return False

def test_market_report():
    """Teste la génération de rapport de marché"""
    print_section("Test de génération de rapport de marché")
    
    try:
        payload = {"location": "global"}
        response = requests.post(
            f"{API_BASE}/market-report",
            json=payload,
            timeout=30
        )
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print_result(True, "Rapport de marché généré avec succès", data)
            return True
        else:
            error_msg = data.get('error', 'Erreur inconnue')
            print_result(False, f"Erreur génération rapport: {error_msg}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result(False, f"Erreur de connexion: {e}")
        return False

def test_daily_news():
    """Teste la récupération des nouvelles quotidiennes"""
    print_section("Test de récupération des nouvelles quotidiennes")
    
    try:
        payload = {"categories": ["market", "crypto", "forex"]}
        response = requests.post(
            f"{API_BASE}/daily-news",
            json=payload,
            timeout=30
        )
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print_result(True, f"{data.get('total_items', 0)} nouvelles récupérées", data)
            return True
        else:
            error_msg = data.get('error', 'Erreur inconnue')
            print_result(False, f"Erreur récupération nouvelles: {error_msg}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result(False, f"Erreur de connexion: {e}")
        return False

def test_financial_markets_search():
    """Teste la recherche de marchés financiers"""
    print_section("Test de recherche de marchés financiers")
    
    try:
        payload = {
            "query": "market news today",
            "search_type": "market_news",
            "max_results": 5,
            "date_restrict": "d1"
        }
        response = requests.post(
            f"{API_BASE}/financial-markets",
            json=payload,
            timeout=30
        )
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print_result(True, f"{data.get('total_results', 0)} résultats trouvés", data)
            return True
        else:
            error_msg = data.get('error', 'Erreur inconnue')
            print_result(False, f"Erreur recherche marchés: {error_msg}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result(False, f"Erreur de connexion: {e}")
        return False

def test_stock_search():
    """Teste la recherche d'actions"""
    print_section("Test de recherche d'actions")
    
    try:
        symbol = "AAPL"
        response = requests.get(
            f"{API_BASE}/stock/{symbol}",
            timeout=30
        )
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print_result(True, f"{data.get('total_results', 0)} résultats trouvés pour {symbol}", data)
            return True
        else:
            error_msg = data.get('error', 'Erreur inconnue')
            print_result(False, f"Erreur recherche action {symbol}: {error_msg}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result(False, f"Erreur de connexion: {e}")
        return False

def test_web_interface():
    """Teste l'interface web"""
    print_section("Test de l'interface web")
    
    try:
        response = requests.get(f"{BASE_URL}/google-search", timeout=10)
        
        if response.status_code == 200:
            print_result(True, "Interface web accessible")
            return True
        else:
            print_result(False, f"Erreur HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result(False, f"Erreur de connexion: {e}")
        return False

def test_integration_with_existing_system():
    """Teste l'intégration avec le système existant"""
    print_section("Test d'intégration avec le système existant")
    
    # Test de l'endpoint de santé général
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            print_result(True, "Système principal opérationnel", data)
            return True
        else:
            print_result(False, f"Erreur système principal: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result(False, f"Erreur de connexion: {e}")
        return False

def run_performance_test():
    """Teste les performances de l'API"""
    print_section("Test de performance")
    
    try:
        start_time = time.time()
        
        # Test de plusieurs requêtes simultanées
        payload = {"location": "global"}
        response = requests.post(
            f"{API_BASE}/market-report",
            json=payload,
            timeout=30
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            print_result(True, f"Rapport généré en {duration:.2f} secondes")
            return duration < 30  # Doit être inférieur à 30 secondes
        else:
            print_result(False, f"Erreur performance: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_result(False, f"Erreur de connexion: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests Google Search API")
    print(f"📡 URL de base: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Résultats des tests
    results = {
        "api_status": False,
        "market_report": False,
        "daily_news": False,
        "financial_markets": False,
        "stock_search": False,
        "web_interface": False,
        "integration": False,
        "performance": False
    }
    
    # Tests
    results["api_status"] = test_api_status()
    
    if results["api_status"]:
        results["market_report"] = test_market_report()
        results["daily_news"] = test_daily_news()
        results["financial_markets"] = test_financial_markets_search()
        results["stock_search"] = test_stock_search()
        results["performance"] = run_performance_test()
    
    results["web_interface"] = test_web_interface()
    results["integration"] = test_integration_with_existing_system()
    
    # Résumé
    print_section("Résumé des tests")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"📊 Tests réussis: {passed_tests}/{total_tests}")
    print(f"📈 Taux de succès: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 Détail des tests:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name.replace('_', ' ').title()}")
    
    if passed_tests == total_tests:
        print("\n🎉 Tous les tests sont passés avec succès!")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) ont échoué")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
        exit(1)
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        exit(1) 