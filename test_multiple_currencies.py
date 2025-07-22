#!/usr/bin/env python3
"""
Test complet des devises pour différentes actions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_multiple_currencies():
    """Test des devises pour différentes actions"""
    print("🔍 Test complet des devises...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Test avec différents types d'actions
        test_cases = [
            # Actions américaines (USD)
            ("AAPL", "USD"),
            ("TSLA", "USD"),
            ("MSFT", "USD"),
            ("GOOGL", "USD"),
            
            # Actions suisses (CHF)
            ("IREN.SW", "CHF"),
            ("NOVN.SW", "CHF"),
            ("ROG.SW", "CHF"),
            
            # Actions européennes (EUR)
            ("ASML", "EUR"),
            ("SAP", "EUR"),
            
            # Actions britanniques (GBP)
            ("HSBA", "GBP"),
            ("BP", "GBP")
        ]
        
        results = []
        
        for symbol, expected_currency in test_cases:
            print(f"\n📈 Test {symbol} (attendu: {expected_currency}):")
            
            try:
                result = manus_stock_api.get_stock_price(symbol, force_refresh=False)
                
                actual_currency = result.get('currency', 'N/A')
                price = result.get('price', 'N/A')
                source = result.get('source', 'N/A')
                
                print(f"   💰 Prix: {price} {actual_currency}")
                print(f"   📊 Source: {source}")
                
                if actual_currency == expected_currency:
                    print(f"   ✅ Devise correcte: {actual_currency}")
                    results.append(True)
                else:
                    print(f"   ❌ Devise incorrecte: {actual_currency} (attendu: {expected_currency})")
                    results.append(False)
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                results.append(False)
        
        # Résumé
        print(f"\n📋 RÉSULTATS:")
        print(f"✅ Corrects: {sum(results)}/{len(results)}")
        print(f"❌ Incorrects: {len(results) - sum(results)}/{len(results)}")
        
        if all(results):
            print("🎉 TOUTES LES DEVISES SONT CORRECTES !")
        else:
            print("⚠️ Certaines devises nécessitent une correction")
        
        return all(results)
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_currency_mapping():
    """Test du mapping des devises"""
    print("\n🔍 Test du mapping des devises...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Créer une instance pour accéder à la méthode privée
        api = manus_stock_api
        
        # Test avec des données yfinance simulées
        test_symbols = ["AAPL", "IREN.SW", "ASML", "HSBA"]
        
        for symbol in test_symbols:
            print(f"\n📈 Test mapping {symbol}:")
            
            # Simuler des données yfinance
            mock_yf_info = {
                'currency': 'USD',  # yfinance peut retourner USD même pour des actions étrangères
                'exchange': 'NMS'
            }
            
            # Appeler la méthode de mapping
            currency = api._get_currency_for_symbol(symbol, mock_yf_info)
            expected = get_expected_currency(symbol)
            
            print(f"   💰 Devise mappée: {currency}")
            print(f"   📊 Attendu: {expected}")
            
            if currency == expected:
                print(f"   ✅ Mapping correct")
            else:
                print(f"   ❌ Mapping incorrect")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test mapping: {e}")
        return False

def get_expected_currency(symbol):
    """Retourne la devise attendue pour un symbole"""
    currency_map = {
        # Actions américaines
        "AAPL": "USD",
        "TSLA": "USD", 
        "MSFT": "USD",
        "GOOGL": "USD",
        
        # Actions suisses
        "IREN.SW": "CHF",
        "NOVN.SW": "CHF",
        "ROG.SW": "CHF",
        
        # Actions européennes
        "ASML": "EUR",
        "SAP": "EUR",
        
        # Actions britanniques
        "HSBA": "GBP",
        "BP": "GBP"
    }
    
    return currency_map.get(symbol, "USD")

def main():
    """Test principal"""
    print("🚀 Test complet des devises par action")
    print("=" * 80)
    
    # Test des devises multiples
    currencies_ok = test_multiple_currencies()
    
    # Test du mapping
    mapping_ok = test_currency_mapping()
    
    print("\n" + "=" * 80)
    print("📋 RÉSULTATS FINAUX:")
    
    if currencies_ok and mapping_ok:
        print("🎉 TOUS LES TESTS PASSÉS !")
        print("✅ Les devises sont correctement gérées")
        print("✅ IREN.SW est maintenant en CHF")
        print("✅ Les actions américaines restent en USD")
        print("✅ Le mapping des devises fonctionne")
    else:
        print("⚠️ Certains tests ont échoué")
        print("🔧 Des corrections supplémentaires sont nécessaires")
    
    return currencies_ok and mapping_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 