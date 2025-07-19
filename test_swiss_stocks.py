#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement des symboles suisses
"""

import requests
import json
import time

def test_yahoo_finance(symbol):
    """Test Yahoo Finance avec un symbole"""
    print(f"\n🔍 Test Yahoo Finance: {symbol}")
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not current_price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        
        if current_price:
            print(f"✅ Yahoo Finance: {current_price} {info.get('currency', 'USD')}")
            return True
        else:
            print(f"❌ Yahoo Finance: Prix non trouvé")
            return False
    except Exception as e:
        print(f"❌ Yahoo Finance: {e}")
        return False

def test_eodhd(symbol, api_key):
    """Test EODHD avec un symbole"""
    print(f"\n🔍 Test EODHD: {symbol}")
    try:
        url = f"https://eodhd.com/api/real-time/{symbol}?api_token={api_key}&fmt=json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 429:
            print(f"❌ EODHD: Rate limit atteint")
            return False
        
        if response.ok:
            data = response.json()
            if data and len(data) > 0:
                quote = data[0] if isinstance(data, list) else data
                current_price = float(quote.get("close", 0))
                if current_price > 0:
                    print(f"✅ EODHD: {current_price} {quote.get('currency', 'USD')}")
                    return True
        
        print(f"❌ EODHD: Données non trouvées (status: {response.status_code})")
        return False
    except Exception as e:
        print(f"❌ EODHD: {e}")
        return False

def test_finnhub(symbol, api_key):
    """Test Finnhub avec un symbole"""
    print(f"\n🔍 Test Finnhub: {symbol}")
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 429:
            print(f"❌ Finnhub: Rate limit atteint")
            return False
        
        if response.ok:
            data = response.json()
            current_price = data.get('c')
            if current_price and current_price > 0:
                print(f"✅ Finnhub: {current_price} USD")
                return True
        
        print(f"❌ Finnhub: Données non trouvées (status: {response.status_code})")
        return False
    except Exception as e:
        print(f"❌ Finnhub: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test des APIs pour les actions suisses")
    print("=" * 50)
    
    # Symboles à tester
    symbols = ["IREN", "IREN.SW"]
    
    # Clés API (utiliser des clés de test si disponibles)
    eodhd_key = "demo"  # Remplacer par votre vraie clé
    finnhub_key = "demo"  # Remplacer par votre vraie clé
    
    for symbol in symbols:
        print(f"\n📊 Test du symbole: {symbol}")
        print("-" * 30)
        
        # Test Yahoo Finance
        yahoo_ok = test_yahoo_finance(symbol)
        
        # Test EODHD
        eodhd_ok = test_eodhd(symbol, eodhd_key)
        
        # Test Finnhub
        finnhub_ok = test_finnhub(symbol, finnhub_key)
        
        # Résumé
        print(f"\n📋 Résumé pour {symbol}:")
        print(f"   Yahoo Finance: {'✅' if yahoo_ok else '❌'}")
        print(f"   EODHD: {'✅' if eodhd_ok else '❌'}")
        print(f"   Finnhub: {'✅' if finnhub_ok else '❌'}")
        
        time.sleep(2)  # Délai entre les tests

if __name__ == "__main__":
    main() 