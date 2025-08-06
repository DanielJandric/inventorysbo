#!/usr/bin/env python3
"""
Test d'exécution du Background Worker
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

async def test_scraper_initialization():
    """Test de l'initialisation du scraper"""
    try:
        logger.info("🧪 Test 1: Initialisation du ScrapingBee Scraper")
        
        from scrapingbee_scraper import get_scrapingbee_scraper
        scraper = get_scrapingbee_scraper()
        
        # Test d'initialisation synchrone
        scraper.initialize_sync()
        logger.info("✅ Initialisation synchrone réussie")
        
        # Test d'initialisation asynchrone
        await scraper.initialize()
        logger.info("✅ Initialisation asynchrone réussie")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation scraper: {e}")
        return False

async def test_task_creation():
    """Test de création de tâche"""
    try:
        logger.info("🧪 Test 2: Création de tâche de scraping")
        
        # Utiliser l'instance globale du scraper
        from app import get_global_scraper
        scraper = get_global_scraper()
        
        # Initialiser
        await scraper.initialize()
        
        # Créer une tâche
        prompt = "Test de création de tâche"
        task_id = await scraper.create_scraping_task(prompt, 2)
        
        logger.info(f"✅ Tâche créée avec l'ID: {task_id}")
        return task_id
        
    except Exception as e:
        logger.error(f"❌ Erreur création tâche: {e}")
        return None

async def test_task_execution(task_id):
    """Test d'exécution de tâche"""
    try:
        logger.info("🧪 Test 3: Exécution de tâche de scraping")
        
        # Utiliser l'instance globale du scraper
        from app import get_global_scraper
        scraper = get_global_scraper()
        
        # Initialiser
        await scraper.initialize()
        
        # Exécuter la tâche
        start_time = time.time()
        result = await scraper.execute_scraping_task(task_id)
        execution_time = time.time() - start_time
        
        logger.info(f"✅ Tâche exécutée en {execution_time:.2f} secondes")
        logger.info(f"📊 Résultat: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur exécution tâche: {e}")
        return None

async def test_database_integration():
    """Test d'intégration avec la base de données"""
    try:
        logger.info("🧪 Test 4: Intégration base de données")
        
        from market_analysis_db import get_market_analysis_db, MarketAnalysis
        
        db = get_market_analysis_db()
        
        if not db.is_connected():
            logger.error("❌ Pas de connexion à la base de données")
            return False
        
        # Créer une analyse de test
        test_analysis = MarketAnalysis(
            analysis_type='test',
            summary='Test d\'intégration',
            key_points=['Test réussi'],
            worker_status='completed'
        )
        
        analysis_id = db.save_analysis(test_analysis)
        
        if analysis_id:
            logger.info(f"✅ Analyse de test sauvegardée avec l'ID: {analysis_id}")
            return True
        else:
            logger.error("❌ Échec de sauvegarde de l'analyse")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur intégration base de données: {e}")
        return False

async def test_full_workflow():
    """Test du workflow complet"""
    try:
        logger.info("🧪 Test 5: Workflow complet")
        
        from app import get_global_scraper
        from market_analysis_db import get_market_analysis_db, MarketAnalysis
        
        # Initialiser le scraper
        scraper = get_global_scraper()
        await scraper.initialize()
        
        # Créer une tâche
        prompt = "Résume moi parfaitement et d'une façon exhaustive la situation sur les marchés financiers aujourd'hui. Aussi, je veux un focus particulier sur l'IA."
        task_id = await scraper.create_scraping_task(prompt, 2)
        
        # Exécuter la tâche
        start_time = time.time()
        result = await scraper.execute_scraping_task(task_id)
        execution_time = time.time() - start_time
        
        if "error" in result:
            logger.error(f"❌ Erreur dans le workflow: {result['error']}")
            return False
        
        # Sauvegarder dans la base de données
        db = get_market_analysis_db()
        analysis = MarketAnalysis(
            analysis_type='test_workflow',
            summary=result.get('summary'),
            key_points=result.get('key_points', []),
            structured_data=result.get('structured_data', {}),
            insights=result.get('insights', []),
            risks=result.get('risks', []),
            opportunities=result.get('opportunities', []),
            sources=result.get('sources', []),
            confidence_score=result.get('confidence_score', 0.0),
            worker_status='completed',
            processing_time_seconds=int(execution_time)
        )
        
        analysis_id = db.save_analysis(analysis)
        
        if analysis_id:
            logger.info(f"✅ Workflow complet réussi - Analyse sauvegardée avec l'ID: {analysis_id}")
            logger.info(f"⏱️ Temps d'exécution: {execution_time:.2f} secondes")
            return True
        else:
            logger.error("❌ Échec de sauvegarde dans le workflow")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur workflow complet: {e}")
        return False

async def main():
    """Fonction principale"""
    logger.info("🚀 Test d'exécution du Background Worker")
    logger.info("=" * 60)
    
    # Test 1: Initialisation
    success1 = await test_scraper_initialization()
    
    # Test 2: Création de tâche
    task_id = await test_task_creation()
    success2 = task_id is not None
    
    # Test 3: Exécution de tâche (si création réussie)
    success3 = False
    if task_id:
        result = await test_task_execution(task_id)
        success3 = result is not None and "error" not in result
    
    # Test 4: Base de données
    success4 = await test_database_integration()
    
    # Test 5: Workflow complet
    success5 = await test_full_workflow()
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 Résultats des tests:")
    logger.info(f"   Test 1 (Initialisation): {'✅' if success1 else '❌'}")
    logger.info(f"   Test 2 (Création tâche): {'✅' if success2 else '❌'}")
    logger.info(f"   Test 3 (Exécution tâche): {'✅' if success3 else '❌'}")
    logger.info(f"   Test 4 (Base de données): {'✅' if success4 else '❌'}")
    logger.info(f"   Test 5 (Workflow complet): {'✅' if success5 else '❌'}")
    
    if all([success1, success2, success3, success4, success5]):
        logger.info("🎉 Tous les tests réussis ! Le Background Worker devrait fonctionner.")
    else:
        logger.error("❌ Certains tests ont échoué. Vérifiez les logs ci-dessus.")
    
    return all([success1, success2, success3, success4, success5])

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 