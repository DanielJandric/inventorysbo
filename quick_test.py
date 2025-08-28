#!/usr/bin/env python3
import asyncio
import os
from scrapingbee_scraper import get_scrapingbee_scraper

async def quick_test():
    print("🧪 Test rapide du scraper (sans Yahoo Finance)")
    print("=" * 50)
    
    # Set dummy API key for testing
    os.environ['SCRAPINGBEE_API_KEY'] = 'test_key_for_testing'
    
    try:
        scraper = get_scrapingbee_scraper()
        scraper.initialize_sync()
        print("✅ Scraper initialisé")
        
        # Test RSS direct (sans ScrapingBee)
        print("\n📰 Test RSS direct...")
        result = await scraper.search_and_scrape_deep(
            'market analysis', 
            per_site=3, 
            max_age_hours=72, 
            min_chars=5000
        )
        
        print(f"📊 Résultats: {len(result)} articles")
        if result:
            print(f"📝 Total chars: {sum(len(r.content) for r in result)}")
            for i, r in enumerate(result[:2]):
                print(f"  {i+1}. {r.title[:60]}... ({r.metadata.get('source', 'unknown')})")
        else:
            print("❌ Aucun article trouvé")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())
