#!/usr/bin/env python3
"""
Test d'intégration Yahoo Finance pour les prix d'actions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_price_manager import StockPriceManager
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_yahoo_finance_integration():
    """Test l'intégration Yahoo Finance"""
    print("🧪 Test d'intégration Yahoo Finance")
    print("=" * 50)
    
    # Initialiser le gestionnaire
    manager = StockPriceManager()
    
    # Test avec quelques symboles
    test_symbols = [
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft Corporation"),
        ("NESN.SW", "Nestlé SA"),
        ("NOVN.SW", "Novartis AG"),
        ("TSLA", "Tesla Inc.")
    ]
    
    for symbol, name in test_symbols:
        print(f"\n📈 Test pour {name} ({symbol})")
        try:
            # Récupérer le prix
            price_data = manager.get_stock_price(symbol, force_refresh=True)
            
            if price_data:
                print(f"✅ Prix récupéré: {price_data.price} {price_data.currency}")
                print(f"   Variation: {price_data.change:+.2f} ({price_data.change_percent:+.2f}%)")
                print(f"   Volume: {price_data.volume:,}")
                print(f"   P/E Ratio: {price_data.pe_ratio or 'N/A'}")
                print(f"   52W High: {price_data.high_52_week or 'N/A'}")
                print(f"   52W Low: {price_data.low_52_week or 'N/A'}")
            else:
                print(f"❌ Aucune donnée trouvée pour {symbol}")
                
        except Exception as e:
            print(f"❌ Erreur pour {symbol}: {e}")
    
    # Test du cache
    print(f"\n💾 Test du cache")
    cache_status = manager.get_cache_status()
    print(f"   Requêtes quotidiennes: {cache_status['daily_requests']}/{cache_status['max_daily_requests']}")
    print(f"   Entrées en cache: {cache_status['cache_entries']}")
    
    print(f"\n✅ Test d'intégration Yahoo Finance terminé")

if __name__ == "__main__":
    test_yahoo_finance_integration() 