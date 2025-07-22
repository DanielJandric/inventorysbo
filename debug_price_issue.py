#!/usr/bin/env python3
"""
Diagnostic du problème des prix à 1.0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_manus_vs_yfinance():
    """Test direct de Manus vs yfinance"""
    print("🔍 Test direct Manus vs yfinance...")
    
    try:
        from manus_integration import manus_stock_api
        
        symbols = ["AAPL", "TSLA", "IREN.SW"]
        
        for symbol in symbols:
            print(f"\n📈 Test {symbol}:")
            
            # Test direct yfinance
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                info = ticker.info
                yf_price = info.get('currentPrice')
                yf_currency = info.get('currency')
                print(f"   🔄 yfinance direct: {yf_price} {yf_currency}")
            except Exception as e:
                print(f"   ❌ yfinance direct: {e}")
            
            # Test via notre API
            result = manus_stock_api.get_stock_price(symbol, force_refresh=True)
            print(f"   📊 Notre API: {result.get('price')} {result.get('currency')}")
            print(f"   📋 Source: {result.get('source')}")
            print(f"   🔍 Status: {result.get('status')}")
            
            if result.get('price') == 1.0:
                print(f"   ⚠️ PROBLÈME: Prix toujours à 1.0!")
            else:
                print(f"   ✅ Prix correct: {result.get('price')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_cache_behavior():
    """Test du comportement du cache"""
    print("\n🔍 Test du comportement du cache...")
    
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
        
        # Troisième appel (force refresh)
        print("   3. Troisième appel (force_refresh=True):")
        result3 = manus_stock_api.get_stock_price(symbol, force_refresh=True)
        print(f"      Prix: {result3.get('price')} {result3.get('currency')}")
        print(f"      Source: {result3.get('source')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test cache: {e}")
        return False

def test_parsing_logic():
    """Test de la logique de parsing"""
    print("\n🔍 Test de la logique de parsing...")
    
    try:
        from manus_integration import manus_stock_api
        
        symbol = "AAPL"
        print(f"\n📈 Test parsing pour {symbol}:")
        
        # Vider le cache
        manus_stock_api.clear_cache()
        
        # Test avec force_refresh
        result = manus_stock_api.get_stock_price(symbol, force_refresh=True)
        
        print(f"   Prix final: {result.get('price')}")
        print(f"   Devise: {result.get('currency')}")
        print(f"   Source: {result.get('source')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Parsing success: {result.get('parsing_success')}")
        print(f"   Fallback reason: {result.get('fallback_reason')}")
        
        if result.get('parsing_success') == False:
            print("   ✅ Parsing Manus échoué (normal)")
            if result.get('source') == 'Yahoo Finance (yfinance)':
                print("   ✅ Fallback yfinance utilisé")
            else:
                print("   ❌ Fallback yfinance non utilisé!")
        else:
            print("   ⚠️ Parsing Manus réussi (anormal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test parsing: {e}")
        return False

def check_manus_api_response():
    """Vérifier la réponse de l'API Manus"""
    print("\n🔍 Vérification réponse API Manus...")
    
    try:
        import requests
        
        symbol = "AAPL"
        base_url = "https://ogh5izcelen1.manus.space"
        
        print(f"\n📈 Test API Manus pour {symbol}:")
        
        # Test différents endpoints
        endpoints = [
            f"/api/stocks/{symbol}",
            f"/stocks/{symbol}",
            f"/api/prices/{symbol}",
            f"/prices/{symbol}"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"   🔗 Test: {url}")
                
                response = requests.get(url, timeout=10)
                print(f"      Status: {response.status_code}")
                print(f"      Content-Length: {len(response.text)}")
                
                if response.status_code == 200:
                    # Chercher des patterns de prix
                    import re
                    price_patterns = [
                        r'price["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
                        r'current-price["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
                        r'[\$€£]?\s*([\d,]+\.?\d*)\s*USD?',
                        r'price["\']?\s*=\s*["\']?([\d,]+\.?\d*)["\']?'
                    ]
                    
                    for pattern in price_patterns:
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        if matches:
                            print(f"      ✅ Pattern trouvé: {matches[:3]}")  # Afficher les 3 premiers
                            break
                    else:
                        print(f"      ❌ Aucun pattern de prix trouvé")
                
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification API: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Diagnostic du problème des prix à 1.0")
    print("=" * 80)
    
    # Test direct
    test_manus_vs_yfinance()
    
    # Test cache
    test_cache_behavior()
    
    # Test parsing
    test_parsing_logic()
    
    # Vérification API
    check_manus_api_response()
    
    print("\n" + "=" * 80)
    print("📋 DIAGNOSTIC TERMINÉ")
    print("🔍 Vérifiez les logs ci-dessus pour identifier le problème")

if __name__ == "__main__":
    main() 