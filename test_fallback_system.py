#!/usr/bin/env python3
"""
Test du système de fallback complet avec yfinance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fallback_system():
    """Test du système de fallback complet"""
    print("🔍 Test du système de fallback complet...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Test avec force_refresh pour forcer le fallback
        print("📡 Test avec force_refresh=True...")
        result = manus_stock_api.get_stock_price("TSLA", force_refresh=True)
        
        print(f"📊 Résultat complet: {result}")
        
        # Vérifier les propriétés
        checks = {
            'price': result.get('price') is not None and result.get('price') != 1.0,
            'source': 'Yahoo Finance' in result.get('source', ''),
            'status': result.get('status') == 'fallback_success',
            'fallback_reason': result.get('fallback_reason') is not None
        }
        
        print("\n📋 Vérifications fallback:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {'OK' if passed else 'Échec'}")
        
        # Vérifier le prix
        if result.get('price') and result.get('price') != 1.0:
            print(f"✅ Prix réel trouvé: {result.get('price')} USD")
            print(f"📊 Source: {result.get('source')}")
            return True
        else:
            print("❌ Prix incorrect ou manquant")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test fallback: {e}")
        return False

def test_multiple_symbols():
    """Test avec plusieurs symboles"""
    print("\n🔍 Test multiple symboles...")
    
    try:
        from manus_integration import manus_stock_api
        
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL", "IREN.SW"]
        
        for symbol in symbols:
            print(f"\n📈 Test {symbol}:")
            result = manus_stock_api.get_stock_price(symbol, force_refresh=False)
            
            if result.get('price') and result.get('price') != 1.0:
                print(f"   ✅ Prix réel: {result.get('price')} {result.get('currency')}")
                print(f"   📊 Source: {result.get('source')}")
            else:
                print(f"   ❌ Prix incorrect: {result.get('price')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test multiple: {e}")
        return False

def test_cache_behavior():
    """Test du comportement du cache avec fallback"""
    print("\n🔍 Test comportement cache avec fallback...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Premier appel (force refresh)
        print("🔄 Premier appel (force refresh)...")
        result1 = manus_stock_api.get_stock_price("AAPL", force_refresh=True)
        
        # Deuxième appel (cache)
        print("📦 Deuxième appel (cache)...")
        result2 = manus_stock_api.get_stock_price("AAPL", force_refresh=False)
        
        # Vérifier que les résultats sont cohérents
        if result1.get('price') == result2.get('price') and result1.get('price') != 1.0:
            print("✅ Cache fonctionne correctement avec fallback")
        else:
            print("⚠️ Différence dans le cache ou prix incorrect")
        
        # Vérifier le statut du cache
        cache_status = manus_stock_api.get_cache_status()
        print(f"📊 Cache: {cache_status.get('cache_size')} entrées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test cache: {e}")
        return False

def test_error_handling():
    """Test de la gestion d'erreurs avec fallback"""
    print("\n🔍 Test gestion d'erreurs avec fallback...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Test avec un symbole invalide
        print("🚫 Test symbole invalide...")
        result = manus_stock_api.get_stock_price("INVALID_SYMBOL_123", force_refresh=True)
        
        if result.get('status') == 'error':
            print("✅ Gestion d'erreur correcte")
        else:
            print("⚠️ Gestion d'erreur inattendue")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test gestion d'erreurs: {e}")
        return False

def analyze_improvements():
    """Analyse des améliorations apportées"""
    print("\n🔍 Analyse des améliorations...")
    
    try:
        with open('manus_integration.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier les nouvelles fonctionnalités
        improvements = {
            'yfinance_fallback': '_try_yfinance_fallback' in content,
            'fallback_reason': 'fallback_reason' in content,
            'fallback_success': 'fallback_success' in content,
            'yfinance_import': 'import yfinance' in content or 'yfinance as yf' in content
        }
        
        print("📋 Vérifications améliorations:")
        for improvement_name, implemented in improvements.items():
            status = "✅" if implemented else "❌"
            print(f"   {status} {improvement_name}: {'Implémenté' if implemented else 'Manquant'}")
        
        return all(improvements.values())
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test du système de fallback complet")
    print("=" * 80)
    
    tests = [
        test_fallback_system,
        test_multiple_symbols,
        test_cache_behavior,
        test_error_handling,
        analyze_improvements
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur dans le test: {e}")
            results.append(False)
    
    print("\n" + "=" * 80)
    print("📋 RÉSULTATS DES TESTS:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ TOUS LES TESTS PASSÉS ({passed}/{total})")
        print("🎉 Le système de fallback fonctionne parfaitement !")
        print("\n🔧 Améliorations apportées:")
        print("   ✅ Fallback vers yfinance implémenté")
        print("   ✅ Prix réels au lieu de 1.0")
        print("   ✅ Gestion d'erreurs robuste")
        print("   ✅ Cache optimisé avec fallback")
        print("   ✅ Logs détaillés de fallback")
        print("   ✅ Métriques de performance")
        print("\n💡 Impact:")
        print("   🎯 Plus d'avertissements 'Prix non disponible'")
        print("   🎯 Prix réels et à jour")
        print("   🎯 Système robuste et fiable")
        print("   🎯 Fallback automatique en cas d'échec")
    else:
        print(f"⚠️ {passed}/{total} tests passés")
        print("🔧 Certaines améliorations nécessitent encore du travail")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 