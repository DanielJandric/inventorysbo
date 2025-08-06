#!/usr/bin/env python3
"""
Test spécifique pour analyser les marchés financiers et l'IA
"""

import asyncio
import json
from scrapingbee_scraper import get_scrapingbee_scraper

async def test_markets_ai():
    """Test d'analyse des marchés financiers et de l'IA"""
    print("📊 Test d'analyse des marchés financiers et de l'IA")
    print("=" * 60)
    
    scraper = get_scrapingbee_scraper()
    
    try:
        # Test d'initialisation
        scraper.initialize_sync()
        
        # Prompt spécifique sur les marchés et l'IA
        prompt = "Résume moi parfaitement et d'une façon exhaustive la situation sur les marchés financiers aujourd'hui. Aussi, je veux un focus particulier sur l'IA."
        
        print("📋 Test 1: Création de tâche")
        task_id = await scraper.create_scraping_task(prompt, 5)
        print(f"✅ Tâche créée: {task_id}")
        
        # Test d'exécution
        print("🚀 Test 2: Exécution de la tâche")
        result = await scraper.execute_scraping_task(task_id)
        
        if "error" in result:
            print(f"❌ Erreur: {result['error']}")
        else:
            print("✅ Résultat obtenu:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(test_markets_ai()) 