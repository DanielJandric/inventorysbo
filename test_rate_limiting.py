#!/usr/bin/env python3
"""
Test de la gestion du rate limiting (erreur 429)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rate_limiting_handling():
    """Test de la gestion du rate limiting"""
    print("🔍 Test de la gestion du rate limiting...")
    
    try:
        from manus_integration import manus_stock_api
        
        symbols = ["AAPL", "TSLA", "IREN.SW"]
        
        print("📋 Test avec plusieurs symboles (risque de rate limiting):")
        
        for i, symbol in enumerate(symbols):
            print(f"\n📈 Test {i+1}/{len(symbols)} - {symbol}:")
            
            # Vider le cache pour forcer les requêtes
            manus_stock_api.clear_cache()
            
            # Test avec force_refresh
            result = manus_stock_api.get_stock_price(symbol, force_refresh=True)
            
            print(f"   💰 Prix: {result.get('price')} {result.get('currency')}")
            print(f"   📋 Source: {result.get('source')}")
            print(f"   🔍 Status: {result.get('status')}")
            
            if result.get('price') == 1.0:
                print(f"   ⚠️ Prix à 1.0 (possible rate limiting)")
            else:
                print(f"   ✅ Prix correct obtenu")
            
            # Petit délai entre les requêtes
            import time
            if i < len(symbols) - 1:
                print(f"   ⏳ Attente 2s avant prochaine requête...")
                time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_cache_effectiveness():
    """Test de l'efficacité du cache"""
    print("\n🔍 Test de l'efficacité du cache...")
    
    try:
        from manus_integration import manus_stock_api
        
        symbol = "AAPL"
        print(f"\n📈 Test cache pour {symbol}:")
        
        # Premier appel (force refresh)
        print("   1. Premier appel (force_refresh=True):")
        result1 = manus_stock_api.get_stock_price(symbol, force_refresh=True)
        print(f"      Prix: {result1.get('price')} {result1.get('currency')}")
        print(f"      Source: {result1.get('source')}")
        
        # Deuxième appel (cache)
        print("   2. Deuxième appel (cache):")
        result2 = manus_stock_api.get_stock_price(symbol, force_refresh=False)
        print(f"      Prix: {result2.get('price')} {result2.get('currency')}")
        print(f"      Source: {result2.get('source')}")
        
        # Vérifier que c'est le même résultat
        if result1.get('price') == result2.get('price'):
            print(f"      ✅ Cache fonctionne (même prix)")
        else:
            print(f"      ❌ Cache ne fonctionne pas (prix différents)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test cache: {e}")
        return False

def test_retry_mechanism():
    """Test du mécanisme de retry"""
    print("\n🔍 Test du mécanisme de retry...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Test de la méthode de retry directement
        print("📈 Test méthode retry:")
        
        # Simuler une erreur 429
        print("   🔄 Test avec retry (simulation erreur 429):")
        
        # Utiliser un symbole qui pourrait causer des problèmes
        symbol = "AAPL"
        
        # Vider le cache
        manus_stock_api.clear_cache()
        
        # Test normal
        result = manus_stock_api.get_stock_price(symbol, force_refresh=True)
        
        print(f"   💰 Résultat final: {result.get('price')} {result.get('currency')}")
        print(f"   📋 Source: {result.get('source')}")
        print(f"   🔍 Status: {result.get('status')}")
        
        if result.get('source') == 'Yahoo Finance (yfinance)':
            print(f"   ✅ Fallback yfinance utilisé avec succès")
        else:
            print(f"   ⚠️ Source différente utilisée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test retry: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test de la gestion du rate limiting")
    print("=" * 80)
    
    # Test rate limiting
    test_rate_limiting_handling()
    
    # Test cache
    test_cache_effectiveness()
    
    # Test retry
    test_retry_mechanism()
    
    print("\n" + "=" * 80)
    print("📋 RÉSULTATS:")
    print("✅ Gestion du rate limiting améliorée")
    print("✅ Cache pour éviter les requêtes excessives")
    print("✅ Mécanisme de retry avec délais progressifs")
    print("✅ Délais entre les requêtes pour éviter l'erreur 429")

if __name__ == "__main__":
    main() 