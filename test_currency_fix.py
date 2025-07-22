#!/usr/bin/env python3
"""
Test et correction de la gestion des devises par action
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_current_currency_handling():
    """Test de la gestion actuelle des devises"""
    print("🔍 Test de la gestion actuelle des devises...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Test avec différents symboles
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL", "IREN.SW"]
        
        for symbol in symbols:
            print(f"\n📈 Test {symbol}:")
            result = manus_stock_api.get_stock_price(symbol, force_refresh=True)
            
            print(f"   💰 Prix: {result.get('price')} {result.get('currency')}")
            print(f"   📊 Source: {result.get('source')}")
            print(f"   🏢 Exchange: {result.get('exchange')}")
            
            # Vérifier la devise
            expected_currency = get_expected_currency(symbol)
            actual_currency = result.get('currency', 'USD')
            
            if actual_currency == expected_currency:
                print(f"   ✅ Devise correcte: {actual_currency}")
            else:
                print(f"   ❌ Devise incorrecte: {actual_currency} (attendu: {expected_currency})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test devises: {e}")
        return False

def get_expected_currency(symbol):
    """Retourne la devise attendue pour un symbole"""
    currency_map = {
        # Actions américaines
        "AAPL": "USD",
        "TSLA": "USD", 
        "MSFT": "USD",
        "GOOGL": "USD",
        "MPW": "USD",
        
        # Actions suisses
        "IREN.SW": "CHF",
        "NOVN.SW": "CHF",
        "ROG.SW": "CHF",
        "NESN.SW": "CHF",
        "UHR.SW": "CHF",
        
        # Actions européennes
        "ASML": "EUR",
        "SAP": "EUR",
        "BMW": "EUR",
        "VOW3": "EUR",
        
        # Actions britanniques
        "HSBA": "GBP",
        "BP": "GBP",
        "GSK": "GBP"
    }
    
    return currency_map.get(symbol, "USD")

def test_yfinance_currency():
    """Test de yfinance pour vérifier les devises"""
    print("\n🔍 Test yfinance pour les devises...")
    
    try:
        import yfinance as yf
        
        symbols = ["AAPL", "IREN.SW", "ASML", "HSBA"]
        
        for symbol in symbols:
            print(f"\n📈 Test yfinance {symbol}:")
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            print(f"   💰 Prix: {info.get('currentPrice')} {info.get('currency', 'N/A')}")
            print(f"   🏢 Exchange: {info.get('exchange', 'N/A')}")
            print(f"   📊 Market: {info.get('market', 'N/A')}")
            
            # Vérifier si yfinance retourne la bonne devise
            yf_currency = info.get('currency')
            expected_currency = get_expected_currency(symbol)
            
            if yf_currency and yf_currency == expected_currency:
                print(f"   ✅ yfinance devise correcte: {yf_currency}")
            else:
                print(f"   ⚠️ yfinance devise: {yf_currency} (attendu: {expected_currency})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test yfinance: {e}")
        return False

def suggest_currency_fix():
    """Suggestions pour corriger la gestion des devises"""
    print("\n💡 Suggestions pour corriger les devises:")
    
    suggestions = [
        "1. Créer un mapping de devises par symbole",
        "2. Modifier _try_yfinance_fallback pour respecter les devises",
        "3. Ajouter une fonction get_currency_for_symbol()",
        "4. Tester avec différents marchés (US, CH, EU, UK)",
        "5. Vérifier que yfinance retourne les bonnes devises",
        "6. Ajouter des logs pour tracer les devises"
    ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")

def main():
    """Test principal"""
    print("🚀 Test de la gestion des devises par action")
    print("=" * 80)
    
    # Test de la gestion actuelle
    test_current_currency_handling()
    
    # Test de yfinance
    test_yfinance_currency()
    
    # Suggestions
    suggest_currency_fix()
    
    print("\n" + "=" * 80)
    print("📋 PROBLÈME IDENTIFIÉ:")
    print("❌ IREN.SW est affiché en USD au lieu de CHF")
    print("❌ Toutes les actions sont forcées en USD")
    print("\n💡 SOLUTION:")
    print("✅ Implémenter un mapping de devises par symbole")
    print("✅ Modifier le fallback yfinance pour respecter les devises")
    print("✅ Tester avec différents marchés")

if __name__ == "__main__":
    main() 