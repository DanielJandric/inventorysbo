#!/usr/bin/env python3
"""
Test du ScrapingBee Scraper
"""

import asyncio
import json
import os
from scrapingbee_scraper import get_scrapingbee_scraper

async def test_scrapingbee_scraper():
    """Test complet du ScrapingBee Scraper"""
    print("🚀 Démarrage des tests du ScrapingBee Scraper")
    
    # Test d'import
    print("🔧 Test d'import")
    try:
        from scrapingbee_scraper import ScrapingBeeScraper
        print("✅ Import réussi")
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return
    
    print("\n🧪 Test du ScrapingBee Scraper")
    print("=" * 50)
    
    scraper = get_scrapingbee_scraper()
    
    try:
        # Test d'initialisation
        print("🔧 Test d'initialisation")
        scraper.initialize_sync()
        print("✅ Initialisation réussie")
        
        # Test de création de tâche
        print("\n📋 Test 1: Création de tâche")
        task_id = await scraper.create_scraping_task("Tesla stock price today latest news earnings", 3)
        print(f"✅ Tâche créée: {task_id}")
        
        # Test d'exécution
        print("\n🚀 Test 2: Exécution de la tâche")
        result = await scraper.execute_scraping_task(task_id)
        
        if "error" in result:
            print(f"❌ Erreur: {result['error']}")
        else:
            print("✅ Résultat obtenu:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Test de statut
        print("\n📊 Test 3: Statut de la tâche")
        task = scraper.get_task_status(task_id)
        if task:
            print(f"✅ Statut: {task.status}")
            print(f"✅ Créé: {task.created_at}")
            print(f"✅ Terminé: {task.completed_at}")
        else:
            print("❌ Tâche non trouvée")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        scraper.cleanup()
        print("\n🧹 ScrapingBee Scraper nettoyé")

if __name__ == "__main__":
    asyncio.run(test_scrapingbee_scraper()) 