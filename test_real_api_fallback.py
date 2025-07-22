#!/usr/bin/env python3
"""
Test d'APIs de prix réelles et implémentation d'un fallback
"""

import requests
import json
from datetime import datetime
import time

def test_yfinance():
    """Test de yfinance (gratuit)"""
    print("🔍 Test yfinance...")
    
    try:
        import yfinance as yf
        
        # Utiliser yfinance (gratuit)
        ticker = yf.Ticker("TSLA")
        info = ticker.info
        
        # Extraire les données importantes
        price_data = {
            'symbol': 'TSLA',
            'price': info.get('currentPrice'),
            'change': info.get('regularMarketChange'),
            'change_percent': info.get('regularMarketChangePercent'),
            'volume': info.get('volume'),
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'high_52_week': info.get('fiftyTwoWeekHigh'),
            'low_52_week': info.get('fiftyTwoWeekLow'),
            'open': info.get('regularMarketOpen'),
            'previous_close': info.get('regularMarketPreviousClose'),
            'currency': 'USD',
            'exchange': info.get('exchange', 'NASDAQ'),
            'source': 'Yahoo Finance (yfinance)'
        }
        
        print(f"✅ yfinance: {price_data}")
        return price_data
        
    except ImportError:
        print("❌ yfinance non installé")
        return None
    except Exception as e:
        print(f"❌ Erreur yfinance: {e}")
        return None

def test_alpha_vantage():
    """Test de l'API Alpha Vantage (gratuite avec clé)"""
    print("\n🔍 Test Alpha Vantage...")
    
    try:
        # Alpha Vantage - API gratuite (500 requêtes/jour)
        api_key = "demo"  # Clé de démonstration
        symbol = "TSLA"
        
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alpha Vantage: {data}")
            return data
        else:
            print(f"❌ Alpha Vantage: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur Alpha Vantage: {e}")
        return None

def test_web_scraping():
    """Test de web scraping simple"""
    print("\n🔍 Test Web Scraping...")
    
    try:
        # Test simple avec une page de prix
        url = "https://finance.yahoo.com/quote/TSLA"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Web scraping: Page accessible ({len(response.text)} caractères)")
            
            # Chercher des patterns de prix
            import re
            price_patterns = [
                r'[\$€£]?\s*([\d,]+\.?\d*)\s*USD?',
                r'price["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
                r'([\d,]+\.?\d*)\s*USD?'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    print(f"   Patterns trouvés: {matches[:5]}")
                    break
            
            return {'status': 'accessible', 'size': len(response.text)}
        else:
            print(f"❌ Web scraping: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur Web scraping: {e}")
        return None

def create_fallback_system():
    """Créer un système de fallback avec plusieurs APIs"""
    print("\n🔧 Création du système de fallback...")
    
    fallback_apis = [
        ("yfinance", test_yfinance),
        ("Web Scraping", test_web_scraping),
        ("Alpha Vantage", test_alpha_vantage)
    ]
    
    for api_name, api_test in fallback_apis:
        print(f"\n🔄 Test {api_name}...")
        try:
            result = api_test()
            if result and result.get('price'):
                print(f"✅ {api_name} fonctionne ! Prix: {result.get('price')}")
                return result
            elif result and result.get('status') == 'accessible':
                print(f"✅ {api_name} accessible pour scraping")
            else:
                print(f"⚠️ {api_name} ne retourne pas de prix valide")
        except Exception as e:
            print(f"❌ {api_name} échoue: {e}")
    
    print("❌ Aucune API de fallback ne fonctionne")
    return None

def suggest_implementation():
    """Suggestions d'implémentation"""
    print("\n💡 Suggestions d'implémentation:")
    
    suggestions = [
        "1. Installer yfinance: pip install yfinance",
        "2. Obtenir une clé API gratuite pour Alpha Vantage",
        "3. Implémenter un système de rotation d'APIs",
        "4. Ajouter un cache pour éviter les limites de rate",
        "5. Implémenter un système de retry automatique",
        "6. Ajouter des métriques de performance par API"
    ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")

def main():
    """Test principal"""
    print("🚀 Test d'APIs de prix réelles et fallback")
    print("=" * 80)
    
    # Tester les APIs
    test_yfinance()
    test_alpha_vantage()
    test_web_scraping()
    
    # Créer le système de fallback
    fallback_result = create_fallback_system()
    
    # Suggestions
    suggest_implementation()
    
    print("\n" + "=" * 80)
    print("📋 RÉSULTATS:")
    
    if fallback_result:
        print(f"✅ Système de fallback créé avec succès !")
        if fallback_result.get('price'):
            print(f"💰 Prix trouvé: {fallback_result.get('price')}")
            print(f"📊 Source: {fallback_result.get('source')}")
        else:
            print(f"📊 Résultat: {fallback_result}")
    else:
        print("❌ Aucun système de fallback fonctionnel trouvé")
        print("💡 Recommandation: Installer yfinance et configurer des clés API")

if __name__ == "__main__":
    main() 