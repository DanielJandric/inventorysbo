#!/usr/bin/env python3
"""
Test de l'API de l'application avec les symboles suisses
"""

import requests
import json
import time

def test_app_api(symbol, base_url="http://localhost:5000"):
    """Test l'API de l'application avec un symbole"""
    print(f"\n🔍 Test API App: {symbol}")
    try:
        url = f"{base_url}/api/stock-price/{symbol}"
        response = requests.get(url, timeout=15)
        
        if response.ok:
            data = response.json()
            if "error" not in data:
                print(f"✅ API App: {data.get('price')} {data.get('currency')}")
                print(f"   Source: {data.get('source')}")
                print(f"   Prix CHF: {data.get('price_chf')} CHF")
                return True
            else:
                print(f"❌ API App: {data.get('error')}")
                return False
        else:
            print(f"❌ API App: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API App: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test de l'API de l'application")
    print("=" * 50)
    
    # Symboles à tester
    symbols = ["IREN", "IREN.SW"]
    
    for symbol in symbols:
        print(f"\n📊 Test du symbole: {symbol}")
        print("-" * 30)
        
        # Test de l'API
        api_ok = test_app_api(symbol)
        
        # Résumé
        print(f"\n📋 Résumé pour {symbol}:")
        print(f"   API App: {'✅' if api_ok else '❌'}")
        
        time.sleep(2)  # Délai entre les tests

if __name__ == "__main__":
    main() 