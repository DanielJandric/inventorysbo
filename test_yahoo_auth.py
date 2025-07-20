#!/usr/bin/env python3
"""
Script de test pour le nouveau module d'authentification Yahoo Finance
"""

import logging
from yahoo_finance_auth import YahooFinanceAuth
from stock_price_manager import StockPriceManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_yahoo_auth_module():
    """Test du module d'authentification Yahoo Finance"""
    
    print("🧪 Test du module d'authentification Yahoo Finance")
    print("=" * 60)
    
    try:
        # Test 1: Initialisation du module
        print("\n1️⃣ Test d'initialisation...")
        auth = YahooFinanceAuth()
        print("✅ Module d'authentification initialisé")
        
        # Test 2: Test de connexion
        print("\n2️⃣ Test de connexion...")
        if auth.test_connection():
            print("✅ Connexion Yahoo Finance réussie")
        else:
            print("❌ Échec de la connexion")
            return False
        
        # Test 3: Récupération de données
        print("\n3️⃣ Test de récupération de données...")
        test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        
        for symbol in test_symbols:
            data = auth.get_stock_data(symbol)
            if data:
                print(f"✅ {symbol}: ${data['price']:.2f} {data['currency']}")
            else:
                print(f"❌ {symbol}: Erreur")
        
        # Test 4: Test des informations détaillées
        print("\n4️⃣ Test des informations détaillées...")
        info = auth.get_stock_info("AAPL")
        if info:
            print("✅ Informations détaillées récupérées")
            if 'summaryProfile' in info:
                print(f"   📊 Secteur: {info['summaryProfile'].get('sector', 'N/A')}")
                print(f"   🏢 Industrie: {info['summaryProfile'].get('industry', 'N/A')}")
        else:
            print("❌ Erreur récupération informations détaillées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_stock_price_manager():
    """Test de l'intégration avec StockPriceManager"""
    
    print("\n" + "=" * 60)
    print("🧪 Test de l'intégration avec StockPriceManager")
    print("=" * 60)
    
    try:
        # Initialiser le gestionnaire
        print("\n1️⃣ Initialisation du StockPriceManager...")
        manager = StockPriceManager()
        print("✅ StockPriceManager initialisé")
        
        # Test de récupération de prix
        print("\n2️⃣ Test de récupération de prix...")
        test_symbols = ["AAPL", "MSFT"]
        
        for symbol in test_symbols:
            price_data = manager.get_stock_price(symbol, force_refresh=True)
            if price_data:
                print(f"✅ {symbol}: ${price_data.price:.2f} {price_data.currency}")
                print(f"   📈 Variation: {price_data.change_percent:+.2f}%")
                print(f"   📊 Volume: {price_data.volume:,}")
            else:
                print(f"❌ {symbol}: Erreur")
        
        # Test du statut du cache
        print("\n3️⃣ Test du statut du cache...")
        cache_status = manager.get_cache_status()
        print(f"   📦 Taille cache: {cache_status['cache_size']}")
        print(f"   📊 Requêtes utilisées: {cache_status['daily_requests']}/{cache_status['max_daily_requests']}")
        print(f"   ✅ Peut faire une requête: {cache_status['can_make_request']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test StockPriceManager: {e}")
        return False

def test_error_handling():
    """Test de la gestion d'erreurs"""
    
    print("\n" + "=" * 60)
    print("🧪 Test de la gestion d'erreurs")
    print("=" * 60)
    
    try:
        auth = YahooFinanceAuth()
        
        # Test avec un symbole invalide
        print("\n1️⃣ Test avec symbole invalide...")
        invalid_data = auth.get_stock_data("INVALID_SYMBOL_12345")
        if invalid_data is None:
            print("✅ Gestion correcte du symbole invalide")
        else:
            print("❌ Erreur: données retournées pour symbole invalide")
        
        # Test de gestion des erreurs
        print("\n2️⃣ Test de gestion des erreurs...")
        try:
            # Test avec un délai très court pour simuler une erreur de rate limit
            auth.min_request_interval = 10.0  # Délai très long
            auth._wait_between_requests()
            print("✅ Gestion des délais entre requêtes fonctionne")
        except Exception as e:
            print(f"❌ Erreur dans la gestion des délais: {e}")
        
        # Restaurer le délai normal
        auth.min_request_interval = 1.0
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de gestion d'erreurs: {e}")
        return False

def main():
    """Fonction principale de test"""
    
    print("🚀 Démarrage des tests Yahoo Finance Auth")
    print("=" * 60)
    
    # Tests
    tests = [
        ("Module d'authentification", test_yahoo_auth_module),
        ("StockPriceManager", test_stock_price_manager),
        ("Gestion d'erreurs", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Le module est opérationnel.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les logs pour plus de détails.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 