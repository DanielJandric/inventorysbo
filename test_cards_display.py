#!/usr/bin/env python3
"""
Test d'affichage des cartes d'actions avec données réelles
"""

import requests
import json
from datetime import datetime

def test_cards_display():
    """Test que les cartes d'actions affichent les données réelles"""
    
    print("🧪 Test d'affichage des cartes d'actions")
    print("=" * 50)
    
    # 1. Récupérer tous les items
    try:
        response = requests.get('http://localhost:5000/api/items')
        if response.status_code != 200:
            print(f"❌ Erreur récupération items: {response.status_code}")
            return
        
        items = response.json()
        stock_items = [item for item in items if item.get('category') == 'Actions' and item.get('stock_symbol')]
        
        print(f"📊 {len(stock_items)} actions trouvées")
        
        if not stock_items:
            print("⚠️ Aucune action trouvée pour le test")
            return
        
        # 2. Tester chaque action
        for item in stock_items[:3]:  # Tester les 3 premières
            symbol = item.get('stock_symbol')
            print(f"\n🔍 Test action: {item.get('name')} ({symbol})")
            
            # Vérifier les données existantes
            current_price = item.get('current_price')
            stock_change_percent = item.get('stock_change_percent')
            last_price_update = item.get('last_price_update')
            
            print(f"   💰 Prix actuel: {current_price}")
            print(f"   📈 Variation %: {stock_change_percent}")
            print(f"   🕒 Dernière mise à jour: {last_price_update}")
            
            # Vérifier si les données sont suffisantes pour l'affichage
            if current_price and stock_change_percent is not None:
                print("   ✅ Données suffisantes pour affichage complet")
                print("   📱 La carte devrait afficher:")
                print(f"      - Prix: {current_price} CHF")
                print(f"      - Variation: {stock_change_percent:+.2f}%")
                print(f"      - Source: API Manus")
                print(f"      - Dernière mise à jour: {last_price_update}")
            else:
                print("   ⚠️ Données insuffisantes - affichage 'Chargement...'")
                
                # Tenter de mettre à jour les prix
                print("   🔄 Tentative de mise à jour...")
                update_response = requests.post(f'http://localhost:5000/api/stock-price/{symbol}')
                if update_response.status_code == 200:
                    update_data = update_response.json()
                    print(f"   ✅ Mise à jour réussie: {update_data.get('price')} {update_data.get('currency')}")
                    print(f"   📊 Variation: {update_data.get('change_percent')}%")
                else:
                    print(f"   ❌ Échec mise à jour: {update_response.status_code}")
        
        # 3. Test de mise à jour globale
        print(f"\n🔄 Test mise à jour globale des prix...")
        update_all_response = requests.post('http://localhost:5000/api/stock-price/update-all')
        if update_all_response.status_code == 200:
            result = update_all_response.json()
            print(f"   ✅ Mise à jour globale réussie")
            print(f"   📊 Actions mises à jour: {len(result.get('success', []))}")
            print(f"   ❌ Échecs: {len(result.get('failed', []))}")
            print(f"   🔄 Source: {result.get('source', 'N/A')}")
        else:
            print(f"   ❌ Échec mise à jour globale: {update_all_response.status_code}")
        
        # 4. Vérifier le statut des APIs
        print(f"\n📊 Statut des APIs...")
        status_response = requests.get('http://localhost:5000/api/stock-price/status')
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   🎯 API Manus: {'✅' if status.get('manus_api', {}).get('available') else '❌'}")
            print(f"   🔄 Yahoo Finance: {'✅' if status.get('yahoo_finance', {}).get('available') else '❌'}")
            print(f"   📈 Source principale: {status.get('primary_source', 'N/A')}")
        else:
            print(f"   ❌ Erreur statut: {status_response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")

if __name__ == "__main__":
    test_cards_display() 