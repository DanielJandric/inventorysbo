#!/usr/bin/env python3
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

async def debug_rss_parsing():
    """Debug RSS parsing to see what's happening"""
    print("🔍 Debug RSS Parsing")
    print("=" * 50)
    
    # Test un flux RSS qui fonctionne
    test_url = 'https://feeds.marketwatch.com/marketwatch/topstories/'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            print(f"📰 Test URL: {test_url}")
            async with session.get(test_url, timeout=10) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    print(f"✅ Status: {resp.status}")
                    print(f"📄 Taille: {len(text)} caractères")
                    print(f"📄 Aperçu: {text[:500]}...")
                    
                    # Parse RSS
                    try:
                        root = ET.fromstring(text)
                        print(f"✅ XML parsé avec succès")
                        print(f"📋 Tag racine: {root.tag}")
                        
                        # Chercher les items
                        items = root.findall('.//item')
                        print(f"📋 Articles trouvés: {len(items)}")
                        
                        if items:
                            # Analyser le premier item
                            first = items[0]
                            print(f"\n📰 Premier article:")
                            print(f"  Tag: {first.tag}")
                            
                            # Analyser tous les sous-éléments
                            for child in first:
                                print(f"  - {child.tag}: {child.text[:100] if child.text else 'None'}...")
                            
                            # Test parsing spécifique
                            link_el = first.find('link')
                            title_el = first.find('title')
                            desc_el = first.find('description')
                            pub_el = first.find('pubDate')
                            
                            print(f"\n🔍 Éléments extraits:")
                            print(f"  Link: {link_el.text if link_el is not None else 'None'}")
                            print(f"  Title: {title_el.text if title_el is not None else 'None'}")
                            print(f"  Description: {desc_el.text[:100] if desc_el and desc_el.text else 'None'}...")
                            print(f"  PubDate: {pub_el.text if pub_el is not None else 'None'}")
                            
                        else:
                            print("❌ Aucun item trouvé")
                            # Chercher d'autres patterns
                            print(f"🔍 Recherche d'autres patterns...")
                            all_elements = root.findall('.//*')
                            print(f"  Total éléments: {len(all_elements)}")
                            for i, elem in enumerate(all_elements[:10]):
                                print(f"  {i}: {elem.tag} = {elem.text[:50] if elem.text else 'None'}...")
                            
                    except Exception as e:
                        print(f"❌ Erreur parsing XML: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"❌ Status: {resp.status}")
                    
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_rss_parsing())
