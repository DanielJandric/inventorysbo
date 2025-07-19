#!/usr/bin/env python3
"""
Script de test pour l'API EODHD
Teste les données disponibles pour les actions suisses et américaines
"""

import os
import requests
import json
from datetime import datetime

# Configuration
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "687ae6e8493e52.65071366")  # Clé par défaut pour test

if not EODHD_API_KEY:
    print("❌ EODHD_API_KEY non configurée")
    print("Définissez la variable d'environnement EODHD_API_KEY")
    exit(1)

def test_eodhd_realtime(symbol):
    """Test l'API temps réel d'EODHD"""
    print(f"\n🔍 Test temps réel pour: {symbol}")
    
    url = f"https://eodhd.com/api/real-time/{symbol}?api_token={EODHD_API_KEY}&fmt=json"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                quote = data[0]
            else:
                quote = data
                
            print("✅ Données temps réel récupérées:")
            print(f"  - Code: {quote.get('code', 'N/A')}")
            print(f"  - Prix de clôture: {quote.get('close', 'N/A')}")
            print(f"  - Devise: {quote.get('currency', 'N/A')}")
            print(f"  - Changement: {quote.get('change', 'N/A')}")
            print(f"  - Changement %: {quote.get('change_p', 'N/A')}")
            print(f"  - Volume: {quote.get('volume', 'N/A')}")
            print(f"  - Volume moyen: {quote.get('avg_volume', 'N/A')}")
            print(f"  - 52W High: {quote.get('high_52_weeks', 'N/A')}")
            print(f"  - 52W Low: {quote.get('low_52_weeks', 'N/A')}")
            print(f"  - Market Cap: {quote.get('market_cap', 'N/A')}")
            print(f"  - Open: {quote.get('open', 'N/A')}")
            print(f"  - High: {quote.get('high', 'N/A')}")
            print(f"  - Low: {quote.get('low', 'N/A')}")
            print(f"  - Previous Close: {quote.get('previous_close', 'N/A')}")
            
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            if response.status_code == 429:
                print("Rate limit atteint")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_eodhd_fundamentals(symbol):
    """Test l'API fondamentales d'EODHD"""
    print(f"\n📊 Test fondamentales pour: {symbol}")
    
    url = f"https://eodhd.com/api/fundamentals/{symbol}?api_token={EODHD_API_KEY}&fmt=json"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            
            if 'General' in data:
                general = data['General']
                print("✅ Données générales récupérées:")
                print(f"  - Nom: {general.get('Name', 'N/A')}")
                print(f"  - Code: {general.get('Code', 'N/A')}")
                print(f"  - Type: {general.get('Type', 'N/A')}")
                print(f"  - Exchange: {general.get('Exchange', 'N/A')}")
                print(f"  - Currency: {general.get('Currency', 'N/A')}")
                print(f"  - Pays: {general.get('Country', 'N/A')}")
                print(f"  - Secteur: {general.get('Sector', 'N/A')}")
                print(f"  - Industrie: {general.get('Industry', 'N/A')}")
                print(f"  - Employés: {general.get('FullTimeEmployees', 'N/A')}")
                print(f"  - Site web: {general.get('WebURL', 'N/A')}")
                
            if 'Highlights' in data:
                highlights = data['Highlights']
                print("\n📈 Données financières:")
                print(f"  - PE Ratio: {highlights.get('PERatio', 'N/A')}")
                print(f"  - PB Ratio: {highlights.get('PBRatio', 'N/A')}")
                print(f"  - Market Cap: {highlights.get('MarketCapitalization', 'N/A')}")
                print(f"  - Enterprise Value: {highlights.get('EnterpriseValue', 'N/A')}")
                print(f"  - EBITDA: {highlights.get('EBITDA', 'N/A')}")
                print(f"  - ROE: {highlights.get('ROE', 'N/A')}")
                print(f"  - ROA: {highlights.get('ROA', 'N/A')}")
                print(f"  - Dividend Yield: {highlights.get('DividendYield', 'N/A')}")
                print(f"  - Payout Ratio: {highlights.get('PayoutRatio', 'N/A')}")
                
            if 'Valuation' in data:
                valuation = data['Valuation']
                print("\n💰 Données de valorisation:")
                print(f"  - Forward PE: {valuation.get('ForwardPE', 'N/A')}")
                print(f"  - PEG Ratio: {valuation.get('PEGRatio', 'N/A')}")
                print(f"  - Price to Sales: {valuation.get('PriceToSalesRatio', 'N/A')}")
                print(f"  - Price to Book: {valuation.get('PriceToBookRatio', 'N/A')}")
                
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            if response.status_code == 429:
                print("Rate limit atteint")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("🧪 Test de l'API EODHD")
    print("=" * 50)
    
    # Test avec des actions suisses
    swiss_symbols = ['NOVN.SW', 'ROG.SW', 'NESN.SW', 'UHRN.SW']
    
    print("\n🇨🇭 Test des actions suisses:")
    for symbol in swiss_symbols:
        test_eodhd_realtime(symbol)
        test_eodhd_fundamentals(symbol)
        print("-" * 30)
    
    # Test avec des actions américaines
    us_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    print("\n🇺🇸 Test des actions américaines:")
    for symbol in us_symbols:
        test_eodhd_realtime(symbol)
        test_eodhd_fundamentals(symbol)
        print("-" * 30)
    
    print("\n✅ Test terminé")

if __name__ == "__main__":
    main() 