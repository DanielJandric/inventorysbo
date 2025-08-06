#!/usr/bin/env python3
"""
Test simple du Background Worker sans dépendance à app.py
"""

import os
import asyncio
import logging
import time
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instance globale du scraper
_global_scraper = None

def get_global_scraper():
    """Retourne l'instance globale du scraper"""
    global _global_scraper
    if _global_scraper is None:
        from scrapingbee_scraper import get_scrapingbee_scraper
        _global_scraper = get_scrapingbee_scraper()
    return _global_scraper

async def test_worker_functionality():
    """Test de la fonctionnalité du Background Worker"""
    try:
        logger.info("🧪 Test du Background Worker avec instance globale")
        
        # Utiliser l'instance globale
        scraper = get_global_scraper()
        
        # Initialiser
        scraper.initialize_sync()
        logger.info("✅ Scraper initialisé")
        
        # Créer une tâche
        prompt = "Résume moi parfaitement et d'une façon exhaustive la situation sur les marchés financiers aujourd'hui. Aussi, je veux un focus particulier sur l'IA."
        task_id = await scraper.create_scraping_task(prompt, 2)
        logger.info(f"✅ Tâche créée: {task_id}")
        
        # Exécuter la tâche
        start_time = time.time()
        result = await scraper.execute_scraping_task(task_id)
        execution_time = time.time() - start_time
        
        logger.info(f"✅ Tâche exécutée en {execution_time:.2f} secondes")
        
        if "error" in result:
            logger.error(f"❌ Erreur: {result['error']}")
            return False
        else:
            logger.info("✅ Analyse réussie!")
            logger.info(f"📊 Résumé: {result.get('summary', 'N/A')[:100]}...")
            logger.info(f"📊 Points clés: {len(result.get('key_points', []))}")
            logger.info(f"📊 Insights: {len(result.get('insights', []))}")
            return True
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False

async def main():
    """Fonction principale"""
    logger.info("🚀 Test simple du Background Worker")
    logger.info("=" * 60)
    
    success = await test_worker_functionality()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("🎉 Test réussi ! Le Background Worker fonctionne.")
    else:
        logger.error("❌ Test échoué.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 