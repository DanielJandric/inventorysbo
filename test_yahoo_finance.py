#!/usr/bin/env python3
"""
Test de l'API Yahoo Finance
"""

import requests
import json
import time

def test_yahoo_finance(symbol, name):
    """Test avec Yahoo Finance"""
    print(f"\n📊 Test Yahoo Finance avec {name} ({symbol})")
    print("=" * 50)
    
    # URL de l'API Yahoo Finance
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    
    # Headers pour simuler un navigateur
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                
                print("✅ Données récupérées:")
                print(f"  Symbole: {meta.get('symbol', 'N/A')}")
                print(f"  Prix actuel: {meta.get('regularMarketPrice', 'N/A')}")
                print(f"  Devise: {meta.get('currency', 'N/A')}")
                print(f"  Changement: {meta.get('regularMarketChange', 'N/A')}")
                print(f"  Changement %: {meta.get('regularMarketChangePercent', 'N/A')}%")
                print(f"  Volume: {meta.get('regularMarketVolume', 'N/A'):,}")
                print(f"  Market Cap: {meta.get('marketCap', 'N/A'):,}")
                print(f"  PE Ratio: {meta.get('trailingPE', 'N/A')}")
                print(f"  PB Ratio: {meta.get('priceToBook', 'N/A')}")
                print(f"  Dividend Yield: {meta.get('trailingAnnualDividendYield', 'N/A')}")
                print(f"  52W High: {meta.get('fiftyTwoWeekHigh', 'N/A')}")
                print(f"  52W Low: {meta.get('fiftyTwoWeekLow', 'N/A')}")
                print(f"  Open: {meta.get('regularMarketOpen', 'N/A')}")
                print(f"  High: {meta.get('regularMarketDayHigh', 'N/A')}")
                print(f"  Low: {meta.get('regularMarketDayLow', 'N/A')}")
                print(f"  Previous Close: {meta.get('previousClose', 'N/A')}")
                
                # Informations supplémentaires
                if 'quoteType' in meta:
                    print(f"  Type: {meta.get('quoteType', 'N/A')}")
                if 'shortName' in meta:
                    print(f"  Nom: {meta.get('shortName', 'N/A')}")
                if 'longName' in meta:
                    print(f"  Nom complet: {meta.get('longName', 'N/A')}")
                if 'sector' in meta:
                    print(f"  Secteur: {meta.get('sector', 'N/A')}")
                if 'industry' in meta:
                    print(f"  Industrie: {meta.get('industry', 'N/A')}")
                
            else:
                print("❌ Aucune donnée trouvée dans la réponse")
                
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_yahoo_finance_quote(symbol, name):
    """Test avec l'endpoint quote de Yahoo Finance"""
    print(f"\n📈 Test Yahoo Finance Quote avec {name} ({symbol})")
    print("=" * 50)
    
    # URL de l'API quote
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            
            if 'quoteResponse' in data and 'result' in data['quoteResponse'] and len(data['quoteResponse']['result']) > 0:
                quote = data['quoteResponse']['result'][0]
                
                print("✅ Données quote récupérées:")
                print(f"  Symbole: {quote.get('symbol', 'N/A')}")
                print(f"  Nom: {quote.get('longName', 'N/A')}")
                print(f"  Prix: {quote.get('regularMarketPrice', 'N/A')}")
                print(f"  Devise: {quote.get('currency', 'N/A')}")
                print(f"  Changement: {quote.get('regularMarketChange', 'N/A')}")
                print(f"  Changement %: {quote.get('regularMarketChangePercent', 'N/A')}%")
                print(f"  Volume: {quote.get('regularMarketVolume', 'N/A'):,}")
                print(f"  Market Cap: {quote.get('marketCap', 'N/A'):,}")
                print(f"  PE Ratio: {quote.get('trailingPE', 'N/A')}")
                print(f"  PB Ratio: {quote.get('priceToBook', 'N/A')}")
                print(f"  Dividend Yield: {quote.get('trailingAnnualDividendYield', 'N/A')}")
                print(f"  52W High: {quote.get('fiftyTwoWeekHigh', 'N/A')}")
                print(f"  52W Low: {quote.get('fiftyTwoWeekLow', 'N/A')}")
                print(f"  Open: {quote.get('regularMarketOpen', 'N/A')}")
                print(f"  High: {quote.get('regularMarketDayHigh', 'N/A')}")
                print(f"  Low: {quote.get('regularMarketDayLow', 'N/A')}")
                print(f"  Previous Close: {quote.get('regularMarketPreviousClose', 'N/A')}")
                print(f"  Secteur: {quote.get('sector', 'N/A')}")
                print(f"  Industrie: {quote.get('industry', 'N/A')}")
                print(f"  Exchange: {quote.get('fullExchangeName', 'N/A')}")
                
            else:
                print("❌ Aucune donnée trouvée dans la réponse")
                
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    print("🧪 Test de l'API Yahoo Finance")
    print("=" * 50)
    
    # Test Apple (américain)
    test_yahoo_finance("AAPL", "Apple")
    time.sleep(1)  # Pause pour éviter le rate limiting
    test_yahoo_finance_quote("AAPL", "Apple")
    
    print("\n" + "="*50)
    
    # Test Novartis (suisse)
    test_yahoo_finance("NOVN.SW", "Novartis")
    time.sleep(1)
    test_yahoo_finance_quote("NOVN.SW", "Novartis")
    
    print("\n✅ Test terminé")

if __name__ == "__main__":
    main() 