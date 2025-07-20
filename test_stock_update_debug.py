#!/usr/bin/env python3
"""
Script de test pour déboguer la mise à jour des actions
"""

from stock_price_manager import StockPriceManager
import json

def test_stock_update():
    """Test de la mise à jour des actions"""
    
    print("🧪 Test de mise à jour des actions")
    print("=" * 50)
    
    # Initialiser le gestionnaire
    stock_manager = StockPriceManager()
    
    # Liste de symboles de test (remplacez par vos vrais symboles)
    test_symbols = [
        "AAPL",    # Apple
        "MSFT",    # Microsoft
        "GOOGL",   # Google
        "TSLA",    # Tesla
        "AMZN"     # Amazon
    ]
    
    print(f"📊 Symboles de test: {test_symbols}")
    print(f"📊 Statut initial: {stock_manager.get_daily_requests_status()}")
    
    # Test de mise à jour
    print("\n🔄 Début de la mise à jour...")
    results = stock_manager.update_all_stocks(test_symbols)
    
    # Affichage des résultats
    print(f"\n✅ Résultats:")
    print(f"   - Succès: {len(results['success'])}")
    print(f"   - Erreurs: {len(results['errors'])}")
    print(f"   - Ignorés: {len(results['skipped'])}")
    print(f"   - Requêtes utilisées: {results.get('requests_used', 0)}")
    
    # Détails des succès
    if results['success']:
        print(f"\n✅ Actions mises à jour:")
        for item in results['success']:
            print(f"   - {item['symbol']}: {item['price']} {item['currency']}")
    
    # Détails des erreurs
    if results['errors']:
        print(f"\n❌ Erreurs:")
        for error in results['errors']:
            print(f"   - {error['symbol']}: {error['error']}")
    
    # Détails des ignorés
    if results['skipped']:
        print(f"\n⚠️ Ignorés:")
        for skipped in results['skipped']:
            print(f"   - {skipped['symbol']}: {skipped['reason']}")
    
    # Statut final
    print(f"\n📊 Statut final: {stock_manager.get_daily_requests_status()}")
    
    return results

def test_single_symbol(symbol):
    """Test d'un seul symbole"""
    
    print(f"\n🧪 Test du symbole: {symbol}")
    print("-" * 30)
    
    stock_manager = StockPriceManager()
    
    # Vérifier le cache
    cache_status = stock_manager.get_cache_status()
    print(f"📊 Cache: {cache_status['cache_size']} entrées")
    
    # Récupérer le prix
    price_data = stock_manager.get_stock_price(symbol)
    
    if price_data:
        print(f"✅ Prix récupéré: {price_data.price} {price_data.currency}")
        print(f"   - Variation: {price_data.change} ({price_data.change_percent}%)")
        print(f"   - Volume: {price_data.volume}")
        print(f"   - 52W High: {price_data.high_52_week}")
        print(f"   - 52W Low: {price_data.low_52_week}")
    else:
        print(f"❌ Aucune donnée pour {symbol}")
    
    return price_data

if __name__ == "__main__":
    # Test de mise à jour globale
    results = test_stock_update()
    
    # Test de symboles individuels
    print("\n" + "=" * 50)
    print("🧪 Tests individuels")
    
    for symbol in ["AAPL", "MSFT", "GOOGL"]:
        test_single_symbol(symbol)
    
    print("\n�� Tests terminés") 