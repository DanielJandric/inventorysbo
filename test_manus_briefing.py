#!/usr/bin/env python3
"""
Test de génération de briefing avec API Manus
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manus_stock_manager import manus_stock_manager
from stock_price_manager import StockPriceManager

def test_manus_briefing_data():
    """Test de récupération des données pour le briefing"""
    print("🧪 Test des données de briefing Manus")
    print("=" * 50)
    
    # Test 1: Indices principaux
    print("\n1️⃣ Indices principaux:")
    indices = ['^GSPC', '^IXIC', '^DJI', '^FCHI', '^GDAXI', '^SSMI']
    market_data = manus_stock_manager.get_multiple_stock_prices(indices)
    
    for symbol, data in market_data.items():
        print(f"   {symbol}: {data.price:.2f} {data.currency} ({data.change_percent:+.2f}%)")
    
    # Test 2: Crypto
    print("\n2️⃣ Crypto:")
    crypto = ['BTC-USD', 'ETH-USD']
    crypto_data = manus_stock_manager.get_multiple_stock_prices(crypto)
    
    for symbol, data in crypto_data.items():
        print(f"   {symbol}: {data.price:.2f} {data.currency} ({data.change_percent:+.2f}%)")
    
    # Test 3: Obligations (via Yahoo)
    print("\n3️⃣ Obligations (Yahoo):")
    bonds = ['^TNX', '^BUND']
    yahoo_manager = StockPriceManager()
    
    for bond in bonds:
        bond_info = yahoo_manager.get_stock_price(bond)
        if bond_info:
            print(f"   {bond}: {bond_info.price:.2f}% ({bond_info.change_percent:+.2f}%)")
        else:
            print(f"   {bond}: Non disponible")
    
    # Test 4: Formatage des données
    print("\n4️⃣ Formatage pour GPT-4o:")
    market_formatted = "📈 INDICES PRINCIPAUX:\n"
    for symbol, data in market_data.items():
        market_formatted += f"   {symbol}: {data.price:.2f} {data.currency} ({data.change_percent:+.2f}%)\n"
    
    crypto_formatted = "🪙 CRYPTOACTIFS:\n"
    for symbol, data in crypto_data.items():
        crypto_formatted += f"   {symbol}: {data.price:.2f} {data.currency} ({data.change_percent:+.2f}%)\n"
    
    print(market_formatted)
    print(crypto_formatted)
    
    print("\n🎯 Test terminé!")
    print(f"   - Indices récupérés: {len(market_data)}/{len(indices)}")
    print(f"   - Crypto récupérés: {len(crypto_data)}/{len(crypto)}")
    
    return True

if __name__ == "__main__":
    test_manus_briefing_data() 