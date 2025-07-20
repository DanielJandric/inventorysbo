#!/usr/bin/env python3
"""
Script de test pour le nouveau gestionnaire de prix d'actions avec Yahoo Finance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_price_manager import StockPriceManager
import json

def test_stock_price_manager():
    """Test du gestionnaire de prix d'actions"""
    print("🧪 Test du gestionnaire de prix d'actions Yahoo Finance")
    print("=" * 60)
    
    # Initialiser le gestionnaire
    manager = StockPriceManager()
    
    # Test 1: Statut du cache
    print("\n1. 📊 Statut du cache:")
    status = manager.get_cache_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    # Test 2: Prix d'une action américaine
    print("\n2. 🇺🇸 Test action américaine (AAPL):")
    try:
        price_data = manager.get_stock_price("AAPL", force_refresh=True)
        if price_data:
            print(f"✅ Prix récupéré: {price_data.price} {price_data.currency}")
            print(f"   Changement: {price_data.change} ({price_data.change_percent:.2f}%)")
            print(f"   Volume: {price_data.volume:,}")
        else:
            print("❌ Échec récupération prix")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Prix d'une action suisse
    print("\n3. 🇨🇭 Test action suisse (NOVN.SW):")
    try:
        price_data = manager.get_stock_price("NOVN", exchange="SWX", force_refresh=True)
        if price_data:
            print(f"✅ Prix récupéré: {price_data.price} {price_data.currency}")
            print(f"   Changement: {price_data.change} ({price_data.change_percent:.2f}%)")
            print(f"   Volume: {price_data.volume:,}")
        else:
            print("❌ Échec récupération prix")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 4: Historique des prix
    print("\n4. 📈 Test historique des prix (AAPL):")
    try:
        history = manager.get_price_history("AAPL", days=7)
        if history:
            print(f"✅ Historique récupéré: {len(history)} entrées")
            for entry in history[-3:]:  # Afficher les 3 dernières entrées
                print(f"   {entry['date']} {entry['time']}: {entry['price']} ({entry['change_percent']:+.2f}%)")
        else:
            print("❌ Aucun historique disponible")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 5: Mise à jour de plusieurs actions
    print("\n5. 🔄 Test mise à jour multiple:")
    try:
        symbols = ["AAPL", "MSFT", "GOOGL"]
        results = manager.update_all_stocks(symbols)
        print(f"✅ Résultats: {len(results['success'])} succès, {len(results['errors'])} erreurs, {len(results['skipped'])} ignorés")
        
        for success in results['success']:
            print(f"   ✅ {success['symbol']}: {success['price']} {success['currency']}")
        
        for error in results['errors']:
            print(f"   ❌ {error['symbol']}: {error['reason']}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 6: Statut final
    print("\n6. 📊 Statut final:")
    final_status = manager.get_cache_status()
    print(json.dumps(final_status, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés!")

if __name__ == "__main__":
    test_stock_price_manager() 