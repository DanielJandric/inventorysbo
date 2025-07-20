#!/usr/bin/env python3
"""
Test d'optimisation Yahoo Finance avec 10 requêtes quotidiennes maximum
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_price_manager import StockPriceManager
import logging
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_optimized_yahoo_finance():
    """Test l'optimisation des 10 requêtes quotidiennes"""
    print("🧪 Test d'optimisation Yahoo Finance (10 requêtes/jour)")
    print("=" * 60)
    
    # Initialiser le gestionnaire
    manager = StockPriceManager()
    
    # Test du statut initial
    print("\n📊 Statut initial:")
    cache_status = manager.get_cache_status()
    print(f"   Cache: {cache_status['cache_size']} entrées")
    print(f"   Requêtes: {cache_status['daily_requests']}/{cache_status['max_daily_requests']}")
    print(f"   Peut faire une requête: {cache_status['can_make_request']}")
    
    # Test avec plusieurs symboles
    test_symbols = [
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft Corporation"),
        ("NESN.SW", "Nestlé SA"),
        ("NOVN.SW", "Novartis AG"),
        ("TSLA", "Tesla Inc."),
        ("GOOGL", "Alphabet Inc."),
        ("AMZN", "Amazon.com Inc."),
        ("META", "Meta Platforms Inc."),
        ("NVDA", "NVIDIA Corporation"),
        ("BRK-B", "Berkshire Hathaway Inc."),
        ("JPM", "JPMorgan Chase & Co."),
        ("V", "Visa Inc.")
    ]
    
    print(f"\n🔄 Test de mise à jour de {len(test_symbols)} symboles:")
    
    # Test de mise à jour optimisée
    results = manager.update_all_stocks([symbol for symbol, _ in test_symbols])
    
    print(f"\n✅ Résultats de la mise à jour optimisée:")
    print(f"   Symboles traités: {len(results['success'])}")
    print(f"   Requêtes utilisées: {results['requests_used']}")
    print(f"   Erreurs: {len(results['errors'])}")
    print(f"   Ignorés (limite): {len(results['skipped'])}")
    
    # Afficher les détails
    print(f"\n📈 Symboles mis à jour via Yahoo Finance:")
    for item in results['success']:
        if item.get('source') == 'Yahoo Finance':
            print(f"   ✅ {item['symbol']}: {item['price']} {item['currency']}")
    
    print(f"\n💾 Symboles depuis le cache:")
    for item in results['success']:
        if item.get('source') == 'Cache':
            print(f"   💾 {item['symbol']}: {item['price']} {item['currency']}")
    
    if results['errors']:
        print(f"\n❌ Erreurs:")
        for error in results['errors']:
            print(f"   ❌ {error['symbol']}: {error['reason']}")
    
    if results['skipped']:
        print(f"\n⚠️ Ignorés (limite atteinte):")
        for skipped in results['skipped']:
            print(f"   ⚠️ {skipped['symbol']}: {skipped['reason']}")
    
    # Test du statut final
    print(f"\n📊 Statut final:")
    cache_status = manager.get_cache_status()
    print(f"   Cache: {cache_status['cache_size']} entrées")
    print(f"   Requêtes: {cache_status['daily_requests']}/{cache_status['max_daily_requests']}")
    print(f"   Peut faire une requête: {cache_status['can_make_request']}")
    
    # Test de récupération depuis le cache
    print(f"\n🧪 Test de récupération depuis le cache:")
    for symbol, name in test_symbols[:3]:
        print(f"\n   Test {name} ({symbol}):")
        price_data = manager.get_stock_price(symbol, force_refresh=False)
        if price_data:
            print(f"      ✅ Prix: {price_data.price} {price_data.currency}")
            print(f"      📊 Volume: {price_data.volume:,}")
            print(f"      📈 P/E: {price_data.pe_ratio or 'N/A'}")
        else:
            print(f"      ❌ Aucune donnée")
    
    print(f"\n✅ Test d'optimisation terminé")
    print(f"💡 Le système utilise maintenant efficacement les 10 requêtes quotidiennes")
    print(f"💡 Les prix sont mis en cache pendant 24h pour éviter les requêtes inutiles")

if __name__ == "__main__":
    test_optimized_yahoo_finance() 