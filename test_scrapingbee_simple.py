#!/usr/bin/env python3
"""
Test simple de ScrapingBee API
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

async def test_scrapingbee_api():
    """Test simple de l'API ScrapingBee"""
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    base_url = "https://app.scrapingbee.com/api/v1"
    
    print(f"🔑 API Key: {api_key[:10]}..." if api_key else "❌ Pas d'API key")
    
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY non configuré")
        return
    
    # Test simple avec une URL basique
    test_url = "https://example.com"
    
    params = {
        'api_key': api_key,
        'url': test_url,
        'render_js': 'true',  # Activer JavaScript comme suggéré
        'premium_proxy': 'false'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"🔍 Test de scraping: {test_url}")
            async with session.get(base_url, params=params) as response:
                print(f"📊 Status: {response.status}")
                print(f"📋 Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ Succès! Taille du contenu: {len(content)} caractères")
                    print(f"📄 Premiers 200 caractères: {content[:200]}")
                else:
                    error_content = await response.text()
                    print(f"❌ Erreur {response.status}: {error_content}")
                    
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_scrapingbee_api()) 