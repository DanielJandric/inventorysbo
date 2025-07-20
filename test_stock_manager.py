#!/usr/bin/env python3
"""
Test de l'intégration avec StockPriceManager
"""

import logging
from stock_price_manager import StockPriceManager

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_stock_manager():
    print("🧪 Test de l'intégration StockPriceManager")
    print("=" * 50)
    
    try:
        # Initialiser le StockPriceManager
        print("1️⃣ Initialisation du StockPriceManager...")
        spm = StockPriceManager()
        print("✅ StockPriceManager initialisé")
        
        # Test avec AAPL
        print("\n2️⃣ Test avec AAPL...")
        data = spm.get_stock_price('AAPL')
        if data:
            print(f"✅ AAPL: ${data.price:.2f} {data.currency}")
            print(f"   📈 Variation: {data.change_percent:+.2f}%")
            print(f"   📊 Volume: {data.volume:,}")
        else:
            print("❌ Aucune donnée pour AAPL")
        
        # Test avec MSFT
        print("\n3️⃣ Test avec MSFT...")
        data = spm.get_stock_price('MSFT')
        if data:
            print(f"✅ MSFT: ${data.price:.2f} {data.currency}")
            print(f"   📈 Variation: {data.change_percent:+.2f}%")
        else:
            print("❌ Aucune donnée pour MSFT")
        
        # Test du statut du cache
        print("\n4️⃣ Statut du cache...")
        status = spm.get_cache_status()
        print(f"   📦 Taille cache: {status['cache_size']}")
        print(f"   📊 Requêtes utilisées: {status['daily_requests']}/10")
        print(f"   ✅ Peut faire une requête: {status['can_make_request']}")
        
        print("\n🎉 Tous les tests sont passés !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stock_manager() 