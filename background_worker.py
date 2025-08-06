#!/usr/bin/env python3
"""
Background Worker pour Render - Traite les analyses de marché en file d'attente
"""

import os
import asyncio
import time
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Imports
from scrapingbee_scraper import get_scrapingbee_scraper
from market_analysis_db import get_market_analysis_db, MarketAnalysis

class MarketAnalysisWorker:
    def __init__(self):
        self.scraper = get_scrapingbee_scraper()
        self.db = get_market_analysis_db()
        self.poll_interval_seconds = 15  # Vérifier les nouvelles tâches toutes les 15 secondes
        self.is_running = False

    def initialize(self):
        """Initialise le worker et ses dépendances."""
        try:
            logger.info("🚀 Initialisation du Background Worker...")
            # Vérification des variables d'environnement
            required = ['SCRAPINGBEE_API_KEY', 'OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
            if any(not os.getenv(var) for var in required):
                raise ValueError(f"Variables d'environnement manquantes: {', '.join(v for v in required if not os.getenv(v))}")

            self.scraper.initialize_sync()
            if not self.db.is_connected():
                raise ConnectionError("Connexion à la base de données impossible.")
            
            self.is_running = True
            logger.info(f"✅ Worker prêt. Intervalle de vérification: {self.poll_interval_seconds}s")
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation fatale: {e}")
            raise

    async def process_task(self, task: MarketAnalysis):
        """Traite une seule tâche d'analyse."""
        start_time = time.time()
        task_id = task.id
        logger.info(f"📊 Prise en charge de la tâche #{task_id}...")

        try:
            # 1. Mettre à jour le statut à "processing"
            self.db.update_analysis_status(task_id, 'processing')

            # 2. Exécuter le scraping et l'analyse LLM
            prompt = task.prompt or "Analyse générale des marchés financiers avec focus sur l'IA."
            
            scraper_task_id = await self.scraper.create_scraping_task(prompt, 3)
            result = await self.scraper.execute_scraping_task(scraper_task_id)

            # 3. Traiter le résultat
            if "error" in result:
                raise ValueError(result['error'])

            processing_time = int(time.time() - start_time)
            
            # 4. Mettre à jour la tâche avec les résultats complets
            update_data = {
                'summary': result.get('summary'),
                'key_points': result.get('key_points', []),
                'structured_data': result.get('structured_data', {}),
                'insights': result.get('insights', []),
                'risks': result.get('risks', []),
                'opportunities': result.get('opportunities', []),
                'sources': result.get('sources', []),
                'confidence_score': result.get('confidence_score', 0.0),
                'worker_status': 'completed',
                'processing_time_seconds': processing_time
            }
            self.db.update_analysis(task_id, update_data)
            logger.info(f"✅ Tâche #{task_id} terminée avec succès en {processing_time}s.")

        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la tâche #{task_id}: {e}")
            processing_time = int(time.time() - start_time)
            self.db.update_analysis(task_id, {
                'worker_status': 'error',
                'error_message': str(e),
                'processing_time_seconds': processing_time
            })

    async def run_continuous_loop(self):
        """Boucle principale qui recherche et traite les tâches."""
        logger.info("🔄 Démarrage de la boucle de traitement des tâches...")
        while self.is_running:
            try:
                # Chercher une tâche en attente
                pending_task = self.db.get_pending_analysis()

                if pending_task:
                    await self.process_task(pending_task)
                else:
                    # Pas de tâche, on attend avant de vérifier à nouveau
                    await asyncio.sleep(self.poll_interval_seconds)

            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle principale: {e}")
                await asyncio.sleep(60) # Attendre plus longtemps en cas d'erreur grave

    def stop(self):
        """Arrête proprement le worker."""
        logger.info("🛑 Arrêt du Background Worker...")
        self.is_running = False
        if hasattr(self.scraper, 'cleanup'):
            self.scraper.cleanup()

async def main():
    """Point d'entrée principal."""
    worker = MarketAnalysisWorker()
    try:
        worker.initialize()
        await worker.run_continuous_loop()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Arrêt initié.")
    except Exception as e:
        logger.error(f"❌ Le worker s'est arrêté en raison d'une erreur fatale: {e}")
    finally:
        worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
