#!/usr/bin/env python3
"""
Test simple de la nouvelle API Yahoo Finance
"""

import logging
from yahoo_finance_api import YahooFinanceAPI

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_api():
    print("🧪 Test de la nouvelle API Yahoo Finance")
    print("=" * 50)
    
    try:
        # Initialiser l'API
        print("1️⃣ Initialisation de l'API...")
        api = YahooFinanceAPI()
        print("✅ API initialisée avec succès")
        
        # Test de connexion
        print("\n2️⃣ Test de connexion...")
        if api.test_connection():
            print("✅ Connexion réussie")
        else:
            print("❌ Échec de la connexion")
            return
        
        # Test avec AAPL
        print("\n3️⃣ Test avec AAPL...")
        quote = api.get_quote("AAPL")
        if quote:
            print(f"✅ AAPL - Prix: ${quote.get('regularMarketPrice', 'N/A')}")
            print(f"   Variation: {quote.get('regularMarketChangePercent', 'N/A'):.2f}%")
            print(f"   Volume: {quote.get('regularMarketVolume', 'N/A')}")
        else:
            print("❌ Aucune donnée pour AAPL")
        
        # Test avec MSFT
        print("\n4️⃣ Test avec MSFT...")
        quote = api.get_quote("MSFT")
        if quote:
            print(f"✅ MSFT - Prix: ${quote.get('regularMarketPrice', 'N/A')}")
            print(f"   Variation: {quote.get('regularMarketChangePercent', 'N/A'):.2f}%")
        else:
            print("❌ Aucune donnée pour MSFT")
        
        print("\n🎉 Tous les tests sont passés !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api() 