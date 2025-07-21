#!/usr/bin/env python3
"""
Test de récupération de données boursières via Gemini + recherche web
Remplacement potentiel pour yfinance et yahooquery
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_gemini_stock_price(symbol: str) -> dict:
    """
    Teste la récupération du prix d'une action via Gemini + recherche web
    """
    print(f"\n🔍 Test Gemini pour {symbol}")
    print("=" * 50)
    
    gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY non configurée")
        return None
    
    # URL Gemini 2.5 Flash avec API v1
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': gemini_api_key
    }
    
    prompt = f"""Prix actuel de {symbol} en JSON:
{{
    "symbol": "{symbol}",
    "price": 123.45,
    "change": 2.5,
    "change_percent": 2.07,
    "volume": 1000000,
    "last_update": "20:30",
    "currency": "USD"
}}"""
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1000
        }
    }
    
    try:
        print(f"🔍 Recherche du prix de {symbol}...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 Structure de réponse: {json.dumps(result, indent=2)}")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                print(f"🔍 Candidate: {candidate}")
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    content = candidate['content']['parts'][0]['text']
                    print(f"✅ Réponse Gemini: {content}")
                    
                    # Essayer de parser le JSON
                    try:
                        # Nettoyer le contenu (enlever markdown, extraire JSON)
                        clean_content = content.strip()
                        
                        # Chercher le JSON dans les blocs markdown
                        if "```json" in clean_content:
                            start = clean_content.find("```json") + 7
                            end = clean_content.find("```", start)
                            if end != -1:
                                json_str = clean_content[start:end].strip()
                            else:
                                json_str = clean_content[start:].strip()
                        else:
                            # Chercher juste le JSON
                            start = clean_content.find("{")
                            end = clean_content.rfind("}") + 1
                            if start != -1 and end != 0:
                                json_str = clean_content[start:end]
                            else:
                                json_str = clean_content
                        
                        stock_data = json.loads(json_str)
                        print(f"✅ Données parsées: {stock_data}")
                        return stock_data
                    except json.JSONDecodeError as e:
                        print(f"❌ Erreur parsing JSON: {e}")
                        print(f"Contenu reçu: {content}")
                        return None
                else:
                    print(f"❌ Structure content/parts manquante: {candidate}")
                    return None
            else:
                print(f"❌ Réponse invalide: {result}")
                return None
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

def test_multiple_stocks():
    """Teste plusieurs actions populaires"""
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    
    results = {}
    
    for symbol in symbols:
        result = test_gemini_stock_price(symbol)
        if result:
            results[symbol] = result
        else:
            print(f"❌ Échec pour {symbol}")
    
    print(f"\n📊 Résultats: {len(results)}/{len(symbols)} actions récupérées")
    return results

def compare_with_yahoo():
    """Compare avec yfinance (si disponible)"""
    try:
        import yfinance as yf
        
        print("\n🔄 Comparaison avec Yahoo Finance")
        print("=" * 50)
        
        symbol = "AAPL"
        
        # Test Gemini
        gemini_result = test_gemini_stock_price(symbol)
        
        # Test Yahoo Finance
        print(f"\n📈 Yahoo Finance pour {symbol}")
        ticker = yf.Ticker(symbol)
        yahoo_data = ticker.info
        
        print(f"Yahoo - Prix: {yahoo_data.get('currentPrice', 'N/A')}")
        print(f"Yahoo - Variation: {yahoo_data.get('regularMarketChangePercent', 'N/A')}%")
        
        if gemini_result:
            print(f"Gemini - Prix: {gemini_result.get('price', 'N/A')}")
            print(f"Gemini - Variation: {gemini_result.get('change_percent', 'N/A')}%")
        
    except ImportError:
        print("⚠️ yfinance non disponible pour la comparaison")

def main():
    """Fonction principale"""
    print("🚀 Test de récupération de données boursières via Gemini")
    print("=" * 60)
    
    # Test simple
    test_gemini_stock_price("AAPL")
    
    # Test multiple
    results = test_multiple_stocks()
    
    # Comparaison (optionnel)
    compare_with_yahoo()
    
    print(f"\n✅ Test terminé - {len(results)} actions récupérées avec succès")

if __name__ == "__main__":
    main() 