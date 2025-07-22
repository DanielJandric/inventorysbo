#!/usr/bin/env python3
"""
Test Alpha Vantage API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_alpha_vantage():
    """Test Alpha Vantage API"""
    print("🔍 Test Alpha Vantage API...")
    
    try:
        from alpha_vantage_fallback import alpha_vantage_fallback
        
        symbols = ["AAPL", "TSLA", "IREN.SW"]
        
        for symbol in symbols:
            print(f"\n📈 Test {symbol}:")
            
            result = alpha_vantage_fallback.get_stock_price(symbol)
            
            if result:
                print(f"   💰 Prix: {result.get('price')} {result.get('currency')}")
                print(f"   📊 Change: {result.get('change')} ({result.get('change_percent')}%)")
                print(f"   📋 Source: {result.get('source')}")
                print(f"   🔍 Status: {result.get('status')}")
                
                if result.get('price') > 0:
                    print(f"   ✅ Prix correct obtenu")
                else:
                    print(f"   ⚠️ Prix invalide")
            else:
                print(f"   ❌ Aucune donnée obtenue")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_integration():
    """Test de l'intégration avec manus_integration"""
    print("\n🔍 Test de l'intégration...")
    
    try:
        from manus_integration import manus_stock_api
        
        symbols = ["AAPL", "TSLA", "IREN.SW"]
        
        for symbol in symbols:
            print(f"\n📈 Test intégration {symbol}:")
            
            # Vider le cache
            manus_stock_api.clear_cache()
            
            # Test avec force_refresh
            result = manus_stock_api.get_stock_price(symbol, force_refresh=True)
            
            print(f"   💰 Prix: {result.get('price')} {result.get('currency')}")
            print(f"   📋 Source: {result.get('source')}")
            print(f"   🔍 Status: {result.get('status')}")
            
            if result.get('price') == 1.0:
                print(f"   ⚠️ Prix à 1.0 (problème)")
            else:
                print(f"   ✅ Prix correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur intégration: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test Alpha Vantage API")
    print("=" * 80)
    
    # Test Alpha Vantage direct
    test1 = test_alpha_vantage()
    
    # Test intégration
    test2 = test_integration()
    
    print("\n" + "=" * 80)
    print("📋 RÉSULTATS:")
    print(f"✅ Test Alpha Vantage: {'PASSÉ' if test1 else 'ÉCHOUÉ'}")
    print(f"✅ Test intégration: {'PASSÉ' if test2 else 'ÉCHOUÉ'}")
    
    if all([test1, test2]):
        print("🎉 ALPHA VANTAGE FONCTIONNE!")
        print("🚀 Prêt pour le déploiement sur Render")
    else:
        print("⚠️ Des corrections sont nécessaires")

if __name__ == "__main__":
    main() 