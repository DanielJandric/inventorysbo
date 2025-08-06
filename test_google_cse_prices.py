#!/usr/bin/env python3
"""
Test et amélioration de l'extraction des prix depuis Google CSE
"""

import re
from google_cse_integration import GoogleCSEIntegration

def test_price_extraction():
    """Test de l'extraction des prix"""
    print("🧪 Test d'extraction des prix Google CSE")
    print("=" * 50)
    
    cse = GoogleCSEIntegration()
    
    # Test avec différentes actions
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    
    for symbol in symbols:
        print(f"\n💰 Test pour {symbol}:")
        
        # Recherche spécifique pour le prix
        query = f"{symbol} stock price today real time"
        response = cse.search(query, num_results=5)
        
        if response and response.results:
            print(f"   📊 {len(response.results)} résultats trouvés")
            
            for i, result in enumerate(response.results[:2], 1):
                print(f"   {i}. {result.title}")
                print(f"      URL: {result.link}")
                print(f"      Snippet: {result.snippet[:150]}...")
                
                # Tester l'extraction de prix
                price = extract_price_from_text(result.snippet, symbol)
                if price:
                    print(f"      ✅ Prix extrait: ${price}")
                else:
                    print(f"      ❌ Aucun prix trouvé")
        else:
            print(f"   ❌ Aucun résultat pour {symbol}")

def extract_price_from_text(text: str, symbol: str) -> str:
    """Extrait le prix du texte avec des patterns améliorés"""
    
    # Patterns pour trouver des prix
    patterns = [
        # $123.45
        r'\$(\d+\.?\d*)',
        # 123.45 USD
        r'(\d+\.?\d*)\s*USD',
        # price: $123.45
        r'price[:\s]*\$?(\d+\.?\d*)',
        # AAPL $123.45
        rf'{symbol}\s*\$(\d+\.?\d*)',
        # $123.45 per share
        r'\$(\d+\.?\d*)\s*per\s*share',
        # trading at $123.45
        r'trading\s+at\s*\$(\d+\.?\d*)',
        # current price $123.45
        r'current\s+price\s*\$(\d+\.?\d*)',
        # stock price $123.45
        r'stock\s+price\s*\$(\d+\.?\d*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Prendre le premier match qui semble être un prix raisonnable
            for match in matches:
                try:
                    price = float(match)
                    if 1 <= price <= 10000:  # Prix raisonnable pour une action
                        return str(price)
                except ValueError:
                    continue
    
    return None

def test_market_data():
    """Test des données de marché"""
    print("\n📊 Test des données de marché")
    print("=" * 30)
    
    cse = GoogleCSEIntegration()
    
    # Test de recherche de données de marché
    queries = [
        "S&P 500 today",
        "NASDAQ composite today",
        "Dow Jones today",
        "market indices today"
    ]
    
    for query in queries:
        print(f"\n🔍 {query}:")
        response = cse.search(query, num_results=3)
        
        if response and response.results:
            for i, result in enumerate(response.results[:2], 1):
                print(f"   {i}. {result.title}")
                print(f"      {result.snippet[:100]}...")
        else:
            print("   ❌ Aucun résultat")

if __name__ == "__main__":
    test_price_extraction()
    test_market_data() 