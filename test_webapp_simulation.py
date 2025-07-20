#!/usr/bin/env python3
"""
Test de simulation webapp avec requêtes simultanées
"""

import logging
import threading
import time
from stock_price_manager import StockPriceManager

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def simulate_webapp_request(spm, symbol, request_id):
    """Simule une requête webapp"""
    try:
        print(f"🔵 Requête #{request_id} pour {symbol} démarrée")
        data = spm.get_stock_price(symbol, force_refresh=True)
        if data:
            print(f"✅ Requête #{request_id} - {symbol}: ${data.price:.2f} {data.currency}")
        else:
            print(f"❌ Requête #{request_id} - {symbol}: Échec")
    except Exception as e:
        print(f"❌ Requête #{request_id} - {symbol}: Erreur {e}")

def test_webapp_simulation():
    print("🧪 Test de simulation webapp avec requêtes simultanées")
    print("=" * 60)
    
    try:
        # Initialiser le StockPriceManager
        print("1️⃣ Initialisation du StockPriceManager...")
        spm = StockPriceManager()
        print("✅ StockPriceManager initialisé")
        
        # Vérifier le statut initial
        print("\n2️⃣ Statut initial:")
        status = spm.get_cache_status()
        print(f"   📊 Requêtes utilisées: {status['daily_requests']}/10")
        print(f"   ✅ Peut faire une requête: {status['can_make_request']}")
        
        # Simuler plusieurs requêtes simultanées
        print("\n3️⃣ Simulation de requêtes simultanées...")
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        threads = []
        
        # Créer des threads pour simuler des requêtes simultanées
        for i, symbol in enumerate(symbols):
            thread = threading.Thread(
                target=simulate_webapp_request,
                args=(spm, symbol, i + 1)
            )
            threads.append(thread)
        
        # Démarrer tous les threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        print(f"\n⏱️ Temps total: {end_time - start_time:.2f} secondes")
        
        # Vérifier le statut final
        print("\n4️⃣ Statut final:")
        status = spm.get_cache_status()
        print(f"   📊 Requêtes utilisées: {status['daily_requests']}/10")
        print(f"   ✅ Peut faire une requête: {status['can_make_request']}")
        
        # Test avec des requêtes supplémentaires (devrait utiliser le cache)
        print("\n5️⃣ Test avec requêtes supplémentaires (devrait utiliser le cache)...")
        for i, symbol in enumerate(symbols[:3]):
            data = spm.get_stock_price(symbol, force_refresh=False)
            if data:
                print(f"✅ Cache - {symbol}: ${data.price:.2f} {data.currency}")
            else:
                print(f"❌ Cache - {symbol}: Échec")
        
        print("\n🎉 Test de simulation webapp terminé !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_webapp_simulation() 