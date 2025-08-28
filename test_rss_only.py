#!/usr/bin/env python3
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

async def test_rss_feeds():
    """Test direct RSS feeds without ScrapingBee"""
    print("🧪 Test des flux RSS directs")
    print("=" * 50)
    
    # Test RSS feeds
    test_feeds = [
        ('Yahoo Finance', 'https://finance.yahoo.com/news/rssindex'),
        ('MarketWatch', 'https://feeds.marketwatch.com/marketwatch/topstories/'),
        ('CNN World', 'https://rss.cnn.com/rss/edition_world.rss'),
        ('Reuters Business', 'https://feeds.reuters.com/reuters/businessNews'),
        ('Bloomberg Markets', 'https://feeds.bloomberg.com/markets/news.rss'),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36'
    }
    
    total_items = 0
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for name, url in test_feeds:
            try:
                print(f"\n📰 Test {name}: {url}")
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        print(f"  ✅ Status: {resp.status}")
                        print(f"  📄 Taille: {len(text)} caractères")
                        
                        # Parse RSS
                        try:
                            root = ET.fromstring(text)
                            items = root.findall('.//item')
                            print(f"  📋 Articles trouvés: {len(items)}")
                            
                            if items:
                                # Show first item details
                                first = items[0]
                                title = first.find('title')
                                link = first.find('link')
                                pub_date = first.find('pubDate')
                                
                                if title is not None:
                                    print(f"  📰 Premier titre: {title.text[:80]}...")
                                if link is not None:
                                    print(f"  🔗 Premier lien: {link.text[:100]}...")
                                if pub_date is not None:
                                    print(f"  📅 Date: {pub_date.text}")
                                
                                total_items += len(items)
                            else:
                                print(f"  ⚠️ Aucun article trouvé")
                                
                        except Exception as e:
                            print(f"  ❌ Erreur parsing RSS: {e}")
                    else:
                        print(f"  ❌ Status: {resp.status}")
                        
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
    
    print(f"\n📊 Résumé: {total_items} articles RSS au total")
    return total_items

if __name__ == "__main__":
    asyncio.run(test_rss_feeds())
