#!/usr/bin/env python3
"""
Test simple pour vérifier que les corrections dans app.py fonctionnent
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test des imports"""
    print("🔍 Test des imports...")
    
    try:
        # Test de l'import de manus_integration
        from manus_integration import manus_stock_api, manus_market_report_api
        print("   ✅ manus_integration importé avec succès")
        
        # Test des fonctions
        from manus_integration import get_stock_price_manus, generate_market_briefing_manus
        print("   ✅ Fonctions importées avec succès")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur import: {e}")
        return False

def test_stock_api():
    """Test de l'API stock"""
    print("\n🔍 Test de l'API stock...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Test du cache status
        cache_status = manus_stock_api.get_cache_status()
        print(f"   ✅ Cache status: {cache_status}")
        
        # Test de l'API status
        api_status = manus_stock_api.get_api_status()
        print(f"   ✅ API status: {api_status}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur API stock: {e}")
        return False

def test_market_api():
    """Test de l'API market"""
    print("\n🔍 Test de l'API market...")
    
    try:
        from manus_integration import manus_market_report_api
        
        # Test du cache status
        cache_status = manus_market_report_api.get_cache_status()
        print(f"   ✅ Cache status: {cache_status}")
        
        # Test de l'API status
        api_status = manus_market_report_api.get_api_status()
        print(f"   ✅ API status: {api_status}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur API market: {e}")
        return False

def test_functions():
    """Test des fonctions wrapper"""
    print("\n🔍 Test des fonctions wrapper...")
    
    try:
        from manus_integration import get_stock_price_manus, generate_market_briefing_manus
        
        # Test de la fonction stock (sans paramètres optionnels)
        stock_data = get_stock_price_manus('AAPL', force_refresh=True)
        print(f"   ✅ Stock data: {stock_data.get('symbol')} - {stock_data.get('price')}")
        
        # Test de la fonction market
        market_data = generate_market_briefing_manus()
        print(f"   ✅ Market data status: {market_data.get('status')}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur fonctions: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test des corrections de l'application")
    print("=" * 50)
    
    # Tests
    test1 = test_imports()
    test2 = test_stock_api()
    test3 = test_market_api()
    test4 = test_functions()
    
    print("\n" + "=" * 50)
    if all([test1, test2, test3, test4]):
        print("✅ Tous les tests passent - Corrections réussies !")
    else:
        print("❌ Certains tests ont échoué")
    
    print("✅ Test terminé") 