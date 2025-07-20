#!/usr/bin/env python3
"""
Test de l'intégration du fallback yahooquery
"""

import logging
from stock_price_manager import StockPriceManager

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_fallback_integration():
    print("🧪 Test de l'intégration du fallback yahooquery")
    print("=" * 60)
    
    try:
        # Initialiser le StockPriceManager
        print("1️⃣ Initialisation du StockPriceManager...")
        spm = StockPriceManager()
        print("✅ StockPriceManager initialisé")
        
        # Vérifier les modules disponibles
        print("\n2️⃣ Modules disponibles:")
        print(f"   📊 Yahoo Finance API: {'✅' if spm.yahoo_auth else '❌'}")
        print(f"   🔄 YahooQuery Fallback: {'✅' if spm.yahoo_fallback else '❌'}")
        
        # Test avec AAPL (force refresh pour tester le fallback)
        print("\n3️⃣ Test avec AAPL (force refresh)...")
        data = spm.get_stock_price('AAPL', force_refresh=True)
        if data:
            print(f"✅ AAPL: ${data.price:.2f} {data.currency}")
            print(f"   📈 Variation: {data.change_percent:+.2f}%")
            print(f"   📊 Volume: {data.volume:,}")
            print(f"   💰 Market Cap: {data.market_cap:,}" if data.market_cap else "   💰 Market Cap: N/A")
        else:
            print("❌ Aucune donnée pour AAPL")
        
        # Test avec MSFT
        print("\n4️⃣ Test avec MSFT...")
        data = spm.get_stock_price('MSFT', force_refresh=True)
        if data:
            print(f"✅ MSFT: ${data.price:.2f} {data.currency}")
            print(f"   📈 Variation: {data.change_percent:+.2f}%")
        else:
            print("❌ Aucune donnée pour MSFT")
        
        # Test du statut du cache
        print("\n5️⃣ Statut du cache...")
        status = spm.get_cache_status()
        print(f"   📦 Taille cache: {status['cache_size']}")
        print(f"   📊 Requêtes utilisées: {status['daily_requests']}/10")
        print(f"   ✅ Peut faire une requête: {status['can_make_request']}")
        
        print("\n🎉 Test d'intégration du fallback terminé !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fallback_integration() 