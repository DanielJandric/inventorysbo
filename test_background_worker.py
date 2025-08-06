#!/usr/bin/env python3
"""
Test du Background Worker - Vérification rapide
"""

import asyncio
import logging
from background_worker import MarketAnalysisWorker

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_worker():
    """Test rapide du worker"""
    print("🧪 Test du Background Worker")
    print("=" * 40)
    
    worker = MarketAnalysisWorker()
    
    try:
        # Test d'initialisation
        print("📋 Test 1: Initialisation")
        worker.initialize()
        print("✅ Initialisation réussie")
        
        # Test d'une seule analyse
        print("📊 Test 2: Analyse de marché")
        success = await worker.run_market_analysis()
        
        if success:
            print("✅ Analyse réussie")
        else:
            print("❌ Analyse échouée")
        
        # Test de la boucle (version courte)
        print("🔄 Test 3: Boucle courte (30 secondes)")
        worker.interval_hours = 0.01  # 36 secondes pour le test
        
        # Lancer la boucle pour 30 secondes seulement
        import asyncio
        try:
            await asyncio.wait_for(worker.run_continuous_loop(), timeout=30)
        except asyncio.TimeoutError:
            print("⏰ Test terminé après 30 secondes")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        worker.stop()
        print("👋 Test terminé")

if __name__ == "__main__":
    asyncio.run(test_worker()) 