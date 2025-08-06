#!/usr/bin/env python3
"""
Background Worker pour Render - ScrapingBee Market Analysis
Ce script tourne en boucle pour générer des analyses de marché automatiquement
"""

import os
import asyncio
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging pour Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log vers stdout pour Render
    ]
)
logger = logging.getLogger(__name__)

# Import du scraper
from scrapingbee_scraper import get_scrapingbee_scraper

class MarketAnalysisWorker:
    def __init__(self):
        self.scraper = get_scrapingbee_scraper()
        self.interval_hours = 4  # Intervalle entre les analyses (4 heures)
        self.is_running = False
        
    def initialize(self):
        """Initialise le worker"""
        try:
            logger.info("🚀 Initialisation du Background Worker...")
            
            # Vérifier les variables d'environnement
            required_vars = ['SCRAPINGBEE_API_KEY', 'OPENAI_API_KEY']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                raise Exception(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
            
            # Initialiser le scraper
            self.scraper.initialize_sync()
            logger.info("✅ Scraper initialisé avec succès")
            
            self.is_running = True
            logger.info(f"✅ Background Worker prêt - Intervalle: {self.interval_hours} heures")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {e}")
            raise
    
    async def run_market_analysis(self):
        """Exécute une analyse de marché complète"""
        try:
            logger.info("📊 Début de l'analyse de marché...")
            
            # Prompt pour l'analyse exhaustive
            prompt = "Résume moi parfaitement et d'une façon exhaustive la situation sur les marchés financiers aujourd'hui. Aussi, je veux un focus particulier sur l'IA. Inclus les indices majeurs, les tendances, les actualités importantes, et les développements technologiques."
            
            # Créer et exécuter la tâche
            task_id = await self.scraper.create_scraping_task(prompt, 3)
            logger.info(f"📋 Tâche créée: {task_id}")
            
            result = await self.scraper.execute_scraping_task(task_id)
            
            if "error" in result:
                logger.error(f"❌ Erreur analyse: {result['error']}")
                return False
            else:
                logger.info("✅ Analyse terminée avec succès")
                
                # Log du résumé pour monitoring
                if 'summary' in result:
                    summary_preview = result['summary'][:200] + "..." if len(result['summary']) > 200 else result['summary']
                    logger.info(f"📝 Résumé: {summary_preview}")
                
                # Log des statistiques
                stats = {
                    'key_points': len(result.get('key_points', [])),
                    'insights': len(result.get('insights', [])),
                    'risks': len(result.get('risks', [])),
                    'opportunities': len(result.get('opportunities', [])),
                    'sources': len(result.get('sources', [])),
                    'confidence': result.get('confidence_score', 0)
                }
                
                logger.info(f"📊 Statistiques: {stats}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            return False
    
    async def run_continuous_loop(self):
        """Boucle principale du worker"""
        logger.info("🔄 Démarrage de la boucle continue...")
        
        while self.is_running:
            try:
                # Exécuter l'analyse
                success = await self.run_market_analysis()
                
                if success:
                    logger.info(f"✅ Analyse réussie - Prochaine analyse dans {self.interval_hours} heures")
                else:
                    logger.warning(f"⚠️ Analyse échouée - Prochaine tentative dans {self.interval_hours} heures")
                
                # Attendre avant la prochaine analyse
                logger.info(f"⏰ Pause de {self.interval_hours} heures...")
                await asyncio.sleep(self.interval_hours * 3600)  # Convertir en secondes
                
            except KeyboardInterrupt:
                logger.info("🛑 Arrêt demandé par l'utilisateur")
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle principale: {e}")
                logger.info("⏰ Attente de 1 heure avant de réessayer...")
                await asyncio.sleep(3600)  # Attendre 1 heure en cas d'erreur
    
    def stop(self):
        """Arrête le worker"""
        logger.info("🛑 Arrêt du Background Worker...")
        self.is_running = False
        self.scraper.cleanup()

async def main():
    """Fonction principale"""
    worker = MarketAnalysisWorker()
    
    try:
        # Initialiser le worker
        worker.initialize()
        
        # Démarrer la boucle continue
        await worker.run_continuous_loop()
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
    finally:
        worker.stop()
        logger.info("👋 Background Worker arrêté")

if __name__ == "__main__":
    print("🚀 Démarrage du Background Worker pour l'analyse de marché...")
    print("=" * 60)
    
    # Lancer le worker
    asyncio.run(main()) 