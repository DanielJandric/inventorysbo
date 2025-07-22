#!/usr/bin/env python3
"""
Test des prix via l'application web
"""

import requests
import json
import time

def test_webapp_prices():
    """Test des prix via l'API web"""
    print("🔍 Test des prix via l'application web...")
    
    # Attendre que l'app démarre
    print("⏳ Attente du démarrage de l'application...")
    time.sleep(3)
    
    symbols = ["AAPL", "TSLA", "IREN.SW"]
    
    for symbol in symbols:
        print(f"\n📈 Test {symbol} via API web:")
        
        try:
            # Test avec force_refresh
            url = f"http://localhost:5000/api/stock-price/{symbol}?force_refresh=true"
            print(f"   🔗 URL: {url}")
            
            response = requests.get(url, timeout=30)
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   💰 Prix: {data.get('data', {}).get('price')} {data.get('data', {}).get('currency')}")
                print(f"   📋 Source: {data.get('data', {}).get('source')}")
                print(f"   🔍 Status: {data.get('data', {}).get('status')}")
                
                price = data.get('data', {}).get('price')
                if price == 1.0:
                    print(f"   ⚠️ PROBLÈME: Prix à 1.0 via web!")
                else:
                    print(f"   ✅ Prix correct via web: {price}")
            else:
                print(f"   ❌ Erreur HTTP: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    return True

def test_direct_api_call():
    """Test direct de l'API sans passer par l'app web"""
    print("\n🔍 Test direct de l'API...")
    
    try:
        from manus_integration import manus_stock_api
        
        symbols = ["AAPL", "TSLA", "IREN.SW"]
        
        for symbol in symbols:
            print(f"\n📈 Test direct {symbol}:")
            
            # Vider le cache
            manus_stock_api.clear_cache()
            
            # Test direct
            result = manus_stock_api.get_stock_price(symbol, force_refresh=True)
            
            print(f"   💰 Prix: {result.get('price')} {result.get('currency')}")
            print(f"   📋 Source: {result.get('source')}")
            print(f"   🔍 Status: {result.get('status')}")
            
            if result.get('price') == 1.0:
                print(f"   ⚠️ PROBLÈME: Prix à 1.0 en direct!")
            else:
                print(f"   ✅ Prix correct en direct: {result.get('price')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test direct: {e}")
        return False

def test_app_integration():
    """Test de l'intégration dans app.py"""
    print("\n🔍 Test de l'intégration dans app.py...")
    
    try:
        # Importer les fonctions de app.py
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Importer les fonctions
        from app import get_stock_price_manus
        
        symbols = ["AAPL", "TSLA", "IREN.SW"]
        
        for symbol in symbols:
            print(f"\n📈 Test app.py {symbol}:")
            
            # Test via la fonction de app.py
            result = get_stock_price_manus(symbol, force_refresh=True)
            
            print(f"   💰 Prix: {result.get('price')} {result.get('currency')}")
            print(f"   📋 Source: {result.get('source')}")
            print(f"   🔍 Status: {result.get('status')}")
            
            if result.get('price') == 1.0:
                print(f"   ⚠️ PROBLÈME: Prix à 1.0 via app.py!")
            else:
                print(f"   ✅ Prix correct via app.py: {result.get('price')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test app.py: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test des prix via l'application web")
    print("=" * 80)
    
    # Test direct
    test_direct_api_call()
    
    # Test app.py
    test_app_integration()
    
    # Test webapp (si disponible)
    try:
        test_webapp_prices()
    except:
        print("\n⚠️ Application web non accessible, test web ignoré")
    
    print("\n" + "=" * 80)
    print("📋 TESTS TERMINÉS")
    print("🔍 Vérifiez les résultats ci-dessus")

if __name__ == "__main__":
    main() 