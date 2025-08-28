#!/usr/bin/env python3
import asyncio
import os
from scrapingbee_scraper import get_scrapingbee_scraper

async def test_scraper():
    print("🧪 Test du ScrapingBee Scraper avec RSS alternatifs")
    print("=" * 60)
    
    # Set dummy API key for testing
    os.environ['SCRAPINGBEE_API_KEY'] = 'test_key_for_testing'
    
    scraper = get_scrapingbee_scraper()
    
    try:
        # Test d'initialisation
        scraper.initialize_sync()
        print("✅ Scraper initialisé")
        
        # Test de deep scraping avec RSS alternatifs
        print("\n📰 Test deep scraping (RSS + fallbacks)...")
        result = await scraper.search_and_scrape_deep(
            'market analysis today', 
            per_site=6, 
            max_age_hours=72, 
            min_chars=10000
        )
        
        print(f"📊 Résultats:")
        print(f"  - Articles trouvés: {len(result)}")
        print(f"  - Total caractères: {sum(len(r.content) for r in result)}")
        
        if result:
            print("\n📋 Aperçu des articles:")
            for i, r in enumerate(result[:5], 1):
                source = r.metadata.get('source', 'unknown')
                print(f"  {i}. {r.title[:80]}...")
                print(f"     Source: {source} | Chars: {len(r.content)}")
                print(f"     URL: {r.url[:100]}...")
                print()
        else:
            print("❌ Aucun article trouvé")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.cleanup()
        # Clean up environment
        if 'SCRAPINGBEE_API_KEY' in os.environ:
            del os.environ['SCRAPINGBEE_API_KEY']

if __name__ == "__main__":
    asyncio.run(test_scraper())
