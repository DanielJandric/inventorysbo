#!/usr/bin/env python3
"""
Script de diagnostic pour le Background Worker
"""

import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_worker_initialization():
    """Test de l'initialisation du worker"""
    try:
        logger.info("🧪 Test d'initialisation du Background Worker...")
        
        from background_worker import MarketAnalysisWorker
        worker = MarketAnalysisWorker()
        
        # Test d'initialisation
        worker.initialize()
        logger.info("✅ Initialisation réussie")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur d'initialisation: {e}")
        return False

async def test_scraper_connection():
    """Test de la connexion ScrapingBee"""
    try:
        logger.info("🧪 Test de connexion ScrapingBee...")
        
        from scrapingbee_scraper import get_scrapingbee_scraper
        scraper = get_scrapingbee_scraper()
        
        # Test d'initialisation
        scraper.initialize_sync()
        logger.info("✅ Scraper initialisé")
        
        # Test de création d'une tâche simple
        task_id = await scraper.create_scraping_task("Test simple", 1)
        logger.info(f"✅ Tâche créée: {task_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur ScrapingBee: {e}")
        return False

async def test_database_connection():
    """Test de la connexion à la base de données"""
    try:
        logger.info("🧪 Test de connexion à la base de données...")
        
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        
        if db.is_connected():
            logger.info("✅ Connexion à la base de données réussie")
            
            # Test de récupération d'une analyse
            latest = db.get_latest_analysis()
            if latest:
                logger.info(f"✅ Dernière analyse trouvée (ID: {latest.id})")
            else:
                logger.info("ℹ️ Aucune analyse trouvée (normal si la table est vide)")
            
            return True
        else:
            logger.error("❌ Échec de connexion à la base de données")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur base de données: {e}")
        return False

async def test_single_analysis():
    """Test d'une analyse complète"""
    try:
        logger.info("🧪 Test d'une analyse complète...")
        
        from background_worker import MarketAnalysisWorker
        worker = MarketAnalysisWorker()
        worker.initialize()
        
        # Exécuter une seule analyse
        success = await worker.run_market_analysis()
        
        if success:
            logger.info("✅ Analyse complète réussie")
        else:
            logger.error("❌ Analyse complète échouée")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Erreur analyse complète: {e}")
        return False

async def check_environment_variables():
    """Vérification des variables d'environnement"""
    logger.info("🧪 Vérification des variables d'environnement...")
    
    required_vars = [
        'SCRAPINGBEE_API_KEY',
        'OPENAI_API_KEY', 
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Masquer la valeur pour la sécurité
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            logger.info(f"✅ {var}: {masked_value}")
        else:
            logger.error(f"❌ {var}: MANQUANT")
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Variables manquantes: {', '.join(missing_vars)}")
        return False
    else:
        logger.info("✅ Toutes les variables d'environnement sont présentes")
        return True

async def main():
    """Fonction principale de diagnostic"""
    logger.info("🔍 Démarrage du diagnostic du Background Worker")
    logger.info("=" * 60)
    
    # Test 1: Variables d'environnement
    logger.info("\n📋 Test 1: Variables d'environnement")
    env_ok = await check_environment_variables()
    
    # Test 2: Connexion base de données
    logger.info("\n📋 Test 2: Connexion base de données")
    db_ok = await test_database_connection()
    
    # Test 3: Connexion ScrapingBee
    logger.info("\n📋 Test 3: Connexion ScrapingBee")
    scraper_ok = await test_scraper_connection()
    
    # Test 4: Initialisation worker
    logger.info("\n📋 Test 4: Initialisation worker")
    worker_ok = await test_worker_initialization()
    
    # Test 5: Analyse complète (seulement si les autres tests passent)
    if env_ok and db_ok and scraper_ok and worker_ok:
        logger.info("\n📋 Test 5: Analyse complète")
        analysis_ok = await test_single_analysis()
    else:
        logger.warning("⚠️ Test 5 ignoré car les tests précédents ont échoué")
        analysis_ok = False
    
    # Résumé
    logger.info("\n" + "=" * 60)
    logger.info("📊 RÉSUMÉ DU DIAGNOSTIC:")
    logger.info(f"   Variables d'environnement: {'✅' if env_ok else '❌'}")
    logger.info(f"   Base de données: {'✅' if db_ok else '❌'}")
    logger.info(f"   ScrapingBee: {'✅' if scraper_ok else '❌'}")
    logger.info(f"   Initialisation worker: {'✅' if worker_ok else '❌'}")
    logger.info(f"   Analyse complète: {'✅' if analysis_ok else '❌'}")
    
    if all([env_ok, db_ok, scraper_ok, worker_ok, analysis_ok]):
        logger.info("🎉 Tous les tests sont passés! Le worker devrait fonctionner.")
    else:
        logger.error("❌ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")

if __name__ == "__main__":
    asyncio.run(main()) 