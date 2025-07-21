#!/usr/bin/env python3
"""
Test de correction IREN américaine vs IREN.SW suisse
"""

import requests
import json
from datetime import datetime

def test_iren_correction():
    """Test que IREN américaine fonctionne correctement"""
    
    print("🧪 Test correction IREN américaine vs IREN.SW")
    print("=" * 50)
    
    # Test 1: IREN américaine (sans .SW)
    print("\n1️⃣ Test IREN américaine:")
    try:
        response = requests.get('http://localhost:5000/api/stock-price/IREN')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ IREN américaine: {data.get('price')} {data.get('currency')}")
            print(f"   📊 Variation: {data.get('change_percent')}%")
            print(f"   🏢 Exchange: {data.get('exchange', 'N/A')}")
            print(f"   📈 Volume: {data.get('volume', 'N/A')}")
        else:
            print(f"   ❌ Erreur IREN américaine: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: IREN.SW suisse (avec .SW)
    print("\n2️⃣ Test IREN.SW suisse:")
    try:
        response = requests.get('http://localhost:5000/api/stock-price/IREN.SW')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ IREN.SW suisse: {data.get('price')} {data.get('currency')}")
            print(f"   📊 Variation: {data.get('change_percent')}%")
            print(f"   🏢 Exchange: {data.get('exchange', 'N/A')}")
            print(f"   📈 Volume: {data.get('volume', 'N/A')}")
        else:
            print(f"   ❌ Erreur IREN.SW: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Comparaison des devises
    print("\n3️⃣ Comparaison des devises:")
    try:
        # IREN américaine
        iren_us = requests.get('http://localhost:5000/api/stock-price/IREN')
        if iren_us.status_code == 200:
            us_data = iren_us.json()
            print(f"   🇺🇸 IREN américaine: {us_data.get('price')} {us_data.get('currency')}")
        
        # IREN.SW suisse
        iren_sw = requests.get('http://localhost:5000/api/stock-price/IREN.SW')
        if iren_sw.status_code == 200:
            sw_data = iren_sw.json()
            print(f"   🇨🇭 IREN.SW suisse: {sw_data.get('price')} {sw_data.get('currency')}")
        
        # Comparaison
        if iren_us.status_code == 200 and iren_sw.status_code == 200:
            print(f"   🔄 Différence de devise: {us_data.get('currency')} vs {sw_data.get('currency')}")
            if us_data.get('currency') != sw_data.get('currency'):
                print("   ✅ Devises différentes - correction réussie!")
            else:
                print("   ⚠️ Même devise - vérifier la logique")
                
    except Exception as e:
        print(f"   ❌ Erreur comparaison: {e}")
    
    # Test 4: Vérification dans la base de données
    print("\n4️⃣ Vérification base de données:")
    try:
        response = requests.get('http://localhost:5000/api/items')
        if response.status_code == 200:
            items = response.json()
            iren_items = [item for item in items if item.get('stock_symbol') and 'IREN' in item.get('stock_symbol')]
            
            for item in iren_items:
                print(f"   📋 {item.get('name')}: {item.get('stock_symbol')} - {item.get('stock_currency', 'N/A')}")
                print(f"      💰 Prix actuel: {item.get('current_price')} {item.get('stock_currency', 'N/A')}")
                print(f"      🏢 Exchange: {item.get('stock_exchange', 'N/A')}")
        else:
            print(f"   ❌ Erreur récupération items: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test IREN terminé!")

if __name__ == "__main__":
    test_iren_correction() 