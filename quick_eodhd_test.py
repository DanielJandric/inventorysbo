#!/usr/bin/env python3
"""
Test rapide de l'API EODHD
"""

import requests
import json

# Clé API
EODHD_API_KEY = "687ae6e8493e52.65071366"

def format_number(value):
    """Formate un nombre avec des virgules"""
    if value is None or value == 'N/A':
        return 'N/A'
    try:
        return f"{int(value):,}"
    except:
        return str(value)

def test_stock(symbol, name):
    """Test avec une action"""
    print(f"\n📊 Test EODHD avec {name} ({symbol})")
    print("=" * 50)
    
    # Test temps réel
    print("\n📈 Données temps réel:")
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
                
            print("✅ Données récupérées:")
            print(f"  Code: {quote.get('code', 'N/A')}")
            print(f"  Prix: {quote.get('close', 'N/A')}")
            print(f"  Devise: {quote.get('currency', 'N/A')}")
            print(f"  Changement: {quote.get('change', 'N/A')}")
            print(f"  Changement %: {quote.get('change_p', 'N/A')}%")
            print(f"  Volume: {format_number(quote.get('volume', 'N/A'))}")
            print(f"  Volume moyen: {format_number(quote.get('avg_volume', 'N/A'))}")
            print(f"  52W High: {quote.get('high_52_weeks', 'N/A')}")
            print(f"  52W Low: {quote.get('low_52_weeks', 'N/A')}")
            print(f"  Market Cap: {format_number(quote.get('market_cap', 'N/A'))}")
            print(f"  Open: {quote.get('open', 'N/A')}")
            print(f"  High: {quote.get('high', 'N/A')}")
            print(f"  Low: {quote.get('low', 'N/A')}")
            
        else:
            print(f"❌ Erreur: {response.status_code}")
            if response.status_code == 429:
                print("Rate limit atteint")
            elif response.status_code == 403:
                print("Accès refusé - vérifiez la clé API")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test fondamentales (seulement pour les actions américaines)
    if not symbol.endswith('.SW'):
        print("\n📊 Données fondamentales:")
        url = f"https://eodhd.com/api/fundamentals/{symbol}?api_token={EODHD_API_KEY}&fmt=json"
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.ok:
                data = response.json()
                
                if 'General' in data:
                    general = data['General']
                    print("✅ Informations générales:")
                    print(f"  Nom: {general.get('Name', 'N/A')}")
                    print(f"  Secteur: {general.get('Sector', 'N/A')}")
                    print(f"  Industrie: {general.get('Industry', 'N/A')}")
                    
                if 'Highlights' in data:
                    highlights = data['Highlights']
                    print("\n💰 Données financières:")
                    print(f"  PE Ratio: {highlights.get('PERatio', 'N/A')}")
                    print(f"  PB Ratio: {highlights.get('PBRatio', 'N/A')}")
                    print(f"  Market Cap: {format_number(highlights.get('MarketCapitalization', 'N/A'))}")
                    print(f"  Dividend Yield: {highlights.get('DividendYield', 'N/A')}%")
                    
            else:
                print(f"❌ Erreur: {response.status_code}")
                if response.status_code == 403:
                    print("Accès refusé aux données fondamentales")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
    else:
        print("\n📊 Données fondamentales: Non disponibles pour les actions suisses")

def main():
    print("🧪 Test rapide de l'API EODHD")
    print("=" * 50)
    
    # Test Apple (américain)
    test_stock("AAPL", "Apple")
    
    # Test Novartis (suisse)
    test_stock("NOVN.SW", "Novartis")
    
    print("\n✅ Test terminé")

if __name__ == "__main__":
    main() 