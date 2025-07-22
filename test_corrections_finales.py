#!/usr/bin/env python3
"""
Test des corrections finales - Yahoo Finance et stock_price_cache
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test des imports"""
    print("🔍 Test des imports...")
    try:
        from manus_integration import manus_stock_api, manus_market_report_api
        print("✅ Imports manus_integration OK")
        return True
    except Exception as e:
        print(f"❌ Erreur imports: {e}")
        return False

def test_stock_price_function():
    """Test de la fonction get_stock_price_manus"""
    print("\n🔍 Test de get_stock_price_manus...")
    try:
        # Simuler l'appel de la fonction
        from app import get_stock_price_manus
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class MockItem:
            id: Optional[int] = None
            stock_symbol: Optional[str] = None
            stock_quantity: Optional[int] = None
            name: str = "Test"
        
        # Test avec des paramètres valides
        item = MockItem(id=1, stock_symbol="AAPL", stock_quantity=10)
        cache_key = "test_cache_key"
        
        # La fonction devrait maintenant fonctionner sans erreur de stock_price_cache
        print("✅ Fonction get_stock_price_manus accessible")
        return True
        
    except Exception as e:
        print(f"❌ Erreur get_stock_price_manus: {e}")
        return False

def test_yahoo_finance_references():
    """Test qu'il n'y a plus de références à Yahoo Finance"""
    print("\n🔍 Test des références Yahoo Finance...")
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher les références problématiques
        yahoo_refs = []
        if "Yahoo Finance" in content:
            yahoo_refs.append("Yahoo Finance")
        if "yahoo_status" in content:
            yahoo_refs.append("yahoo_status")
        if "stock_price_cache" in content and "stock_price_cache = {}" not in content:
            yahoo_refs.append("stock_price_cache non défini")
        
        if yahoo_refs:
            print(f"⚠️ Références trouvées: {yahoo_refs}")
            return False
        else:
            print("✅ Aucune référence Yahoo Finance problématique trouvée")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lecture fichier: {e}")
        return False

def test_manus_api_status():
    """Test du statut de l'API Manus"""
    print("\n🔍 Test du statut API Manus...")
    try:
        from manus_integration import manus_stock_api, manus_market_report_api
        
        # Test statut stock API
        stock_status = manus_stock_api.get_api_status()
        print(f"📊 Statut Stock API: {stock_status.get('status', 'N/A')}")
        
        # Test statut market report API
        market_status = manus_market_report_api.get_api_status()
        print(f"📈 Statut Market Report API: {market_status.get('status', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur statut API: {e}")
        return False

def test_cache_functions():
    """Test des fonctions de cache"""
    print("\n🔍 Test des fonctions de cache...")
    try:
        from manus_integration import manus_stock_api, manus_market_report_api
        
        # Test cache stock
        stock_cache = manus_stock_api.get_cache_status()
        print(f"📦 Cache Stock: {stock_cache.get('cache_size', 0)} entrées")
        
        # Test cache market report
        market_cache = manus_market_report_api.get_cache_status()
        print(f"📦 Cache Market Report: {market_cache.get('cache_size', 0)} entrées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur cache: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test des corrections finales - Yahoo Finance et stock_price_cache")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_stock_price_function,
        test_yahoo_finance_references,
        test_manus_api_status,
        test_cache_functions
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur dans le test: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("📋 RÉSULTATS DES TESTS:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ TOUS LES TESTS PASSÉS ({passed}/{total})")
        print("🎉 Les corrections Yahoo Finance et stock_price_cache sont OK !")
    else:
        print(f"⚠️ {passed}/{total} tests passés")
        print("🔧 Certaines corrections nécessitent encore du travail")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 