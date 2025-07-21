#!/usr/bin/env python3
"""
Test d'intégration de l'API Manus dans l'application
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manus_stock_manager import manus_stock_manager
from stock_price_manager import StockPriceManager

def test_manus_integration():
    """Test complet de l'intégration Manus"""
    print("🧪 Test d'intégration Manus API")
    print("=" * 60)
    
    # Test 1: Actions US
    print("\n1️⃣ Test actions US (AAPL, MSFT, TSLA):")
    us_symbols = ['AAPL', 'MSFT', 'TSLA']
    us_results = manus_stock_manager.get_multiple_stock_prices(us_symbols)
    
    for symbol, data in us_results.items():
        print(f"   {symbol}: ${data.price:.2f} ({data.change_percent:+.2f}%) - {data.currency}")
    
    # Test 2: Actions suisses
    print("\n2️⃣ Test actions suisses (IREN.SW, NESN.SW, ROG.SW):")
    ch_symbols = ['IREN.SW', 'NESN.SW', 'ROG.SW']
    ch_results = manus_stock_manager.get_multiple_stock_prices(ch_symbols, exchange='SWX')
    
    for symbol, data in ch_results.items():
        print(f"   {symbol}: {data.price:.2f} {data.currency} ({data.change_percent:+.2f}%)")
    
    # Test 3: Test individuel avec exchange
    print("\n3️⃣ Test individuel IREN.SW avec exchange:")
    iren_data = manus_stock_manager.get_stock_price('IREN.SW', exchange='SWX')
    if iren_data:
        print(f"   IREN.SW: {iren_data.price:.2f} {iren_data.currency}")
        print(f"   Exchange: {iren_data.exchange}")
        print(f"   Volume: {iren_data.volume:,}")
        print(f"   Change: {iren_data.change:+.2f} ({iren_data.change_percent:+.2f}%)")
    
    # Test 4: Cache status
    print("\n4️⃣ Statut du cache:")
    cache_status = manus_stock_manager.get_cache_status()
    print(f"   Taille cache: {cache_status['cache_size']}")
    print(f"   Durée cache: {cache_status['cache_duration']}s")
    print(f"   Symboles en cache: {cache_status['cached_symbols']}")
    
    # Test 5: Comparaison avec Yahoo
    print("\n5️⃣ Comparaison Manus vs Yahoo (AAPL):")
    yahoo_manager = StockPriceManager()
    
    manus_aapl = manus_stock_manager.get_stock_price('AAPL')
    yahoo_aapl = yahoo_manager.get_stock_price('AAPL')
    
    if manus_aapl and yahoo_aapl:
        print(f"   Manus: ${manus_aapl.price:.2f} ({manus_aapl.change_percent:+.2f}%)")
        print(f"   Yahoo: ${yahoo_aapl.price:.2f} ({yahoo_aapl.change_percent:+.2f}%)")
        price_diff = abs(manus_aapl.price - yahoo_aapl.price)
        print(f"   Différence: ${price_diff:.2f}")
    else:
        print("   ❌ Données manquantes pour la comparaison")
    
    # Test 6: Test de fallback
    print("\n6️⃣ Test de fallback (symbole inexistant):")
    fake_symbol = 'FAKE123'
    fake_data = manus_stock_manager.get_stock_price(fake_symbol)
    if fake_data:
        print(f"   {fake_symbol}: {fake_data.price}")
    else:
        print(f"   {fake_symbol}: Non trouvé (comportement attendu)")
    
    print("\n🎯 Test d'intégration terminé!")
    print("\n📊 Résumé:")
    print(f"   - Actions US testées: {len(us_results)}/{len(us_symbols)}")
    print(f"   - Actions CH testées: {len(ch_results)}/{len(ch_symbols)}")
    print(f"   - Cache actif: {cache_status['cache_size']} entrées")
    
    return True

if __name__ == "__main__":
    test_manus_integration() 