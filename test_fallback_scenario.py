#!/usr/bin/env python3
"""
Test du scénario de fallback (simulation d'erreur API)
"""

import logging
from stock_price_manager import StockPriceManager

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_fallback_scenario():
    print("🧪 Test du scénario de fallback")
    print("=" * 50)
    
    try:
        # Initialiser le StockPriceManager
        print("1️⃣ Initialisation du StockPriceManager...")
        spm = StockPriceManager()
        print("✅ StockPriceManager initialisé")
        
        # Simuler une erreur en désactivant temporairement l'API principale
        print("\n2️⃣ Simulation d'erreur API principale...")
        original_yahoo_auth = spm.yahoo_auth
        spm.yahoo_auth = None  # Désactiver l'API principale
        
        # Test avec GOOGL (devrait utiliser le fallback)
        print("\n3️⃣ Test avec GOOGL (devrait utiliser yahooquery)...")
        data = spm.get_stock_price('GOOGL', force_refresh=True)
        if data:
            print(f"✅ GOOGL: ${data.price:.2f} {data.currency}")
            print(f"   📈 Variation: {data.change_percent:+.2f}%")
            print(f"   📊 Volume: {data.volume:,}")
            print("   🔄 Source: YahooQuery Fallback")
        else:
            print("❌ Aucune donnée pour GOOGL")
        
        # Restaurer l'API principale
        spm.yahoo_auth = original_yahoo_auth
        
        # Test avec TSLA (devrait utiliser l'API principale)
        print("\n4️⃣ Test avec TSLA (API principale restaurée)...")
        data = spm.get_stock_price('TSLA', force_refresh=True)
        if data:
            print(f"✅ TSLA: ${data.price:.2f} {data.currency}")
            print(f"   📈 Variation: {data.change_percent:+.2f}%")
            print("   🔄 Source: Yahoo Finance API")
        else:
            print("❌ Aucune donnée pour TSLA")
        
        print("\n🎉 Test du scénario de fallback terminé !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fallback_scenario() 