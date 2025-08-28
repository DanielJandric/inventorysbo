#!/usr/bin/env python3
import asyncio
import os
import sys
from datetime import datetime

async def test_rss_fix():
    """Test et correction du scraper RSS"""
    print("🔧 Test et correction du scraper RSS")
    print("=" * 50)
    
    try:
        # Test 1: Vérifier que le scraper peut être importé
        from scrapingbee_scraper import get_scrapingbee_scraper
        print("✅ Import du scraper réussi")
        
        # Test 2: Test RSS direct simple
        scraper = get_scrapingbee_scraper()
        scraper.initialize_sync()
        print("✅ Scraper initialisé")
        
        # Test 3: Test RSS avec une clé factice
        os.environ['SCRAPINGBEE_API_KEY'] = 'test_key_for_testing'
        
        print("\n📰 Test RSS direct...")
        result = await scraper.search_and_scrape_deep(
            'market analysis', 
            per_site=2, 
            max_age_hours=72, 
            min_chars=1000
        )
        
        print(f"📊 Résultats RSS: {len(result)} articles")
        if result:
            print(f"📝 Total chars: {sum(len(r.content) for r in result)}")
            for i, r in enumerate(result[:2]):
                print(f"  {i+1}. {r.title[:60]}... ({r.metadata.get('source', 'unknown')})")
        else:
            print("❌ Aucun article RSS trouvé")
            
    except Exception as e:
        print(f"❌ Erreur RSS: {e}")
        import traceback
        traceback.print_exc()

async def test_stock_data():
    """Test de la récupération de cours de bourse"""
    print("\n📈 Test récupération cours de bourse")
    print("=" * 50)
    
    try:
        # Test 1: Vérifier que stock_api_manager peut être importé
        from stock_api_manager import stock_api_manager
        print("✅ Import stock_api_manager réussi")
        
        # Test 2: Test récupération snapshot
        print("📊 Test get_market_snapshot...")
        snapshot = stock_api_manager.get_market_snapshot()
        
        if snapshot and isinstance(snapshot, dict):
            print("✅ Snapshot récupéré avec succès")
            print(f"📋 Structure: {list(snapshot.keys())}")
            
            # Vérifier quelques données
            if 'stocks' in snapshot and snapshot['stocks']:
                print(f"📈 Actions: {len(snapshot['stocks'])} symboles")
            if 'indices' in snapshot and snapshot['indices']:
                print(f"📊 Indices: {len(snapshot['indices'])} symboles")
        else:
            print("❌ Snapshot invalide ou vide")
            
    except Exception as e:
        print(f"❌ Erreur stock data: {e}")
        import traceback
        traceback.print_exc()

async def test_worker():
    """Test du worker"""
    print("\n⚙️ Test du worker")
    print("=" * 50)
    
    try:
        # Test 1: Vérifier que le worker peut être importé
        from background_worker import MarketAnalysisWorker
        print("✅ Import worker réussi")
        
        # Test 2: Test initialisation worker
        worker = MarketAnalysisWorker()
        print("✅ Worker créé")
        
        # Test 3: Test initialisation
        worker.initialize()
        print("✅ Worker initialisé")
        
    except Exception as e:
        print(f"❌ Erreur worker: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Test principal"""
    print("🧪 Test complet du système")
    print("=" * 60)
    
    await test_rss_fix()
    await test_stock_data()
    await test_worker()
    
    print("\n" + "=" * 60)
    print("🏁 Tests terminés")

if __name__ == "__main__":
    asyncio.run(main())

