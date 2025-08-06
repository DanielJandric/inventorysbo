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

# Import du scraper et de la base de données
from scrapingbee_scraper import get_scrapingbee_scraper
from market_analysis_db import get_market_analysis_db, MarketAnalysis

class MarketAnalysisWorker:
    def __init__(self):
        self.scraper = get_scrapingbee_scraper()
        self.db = get_market_analysis_db()
        self.interval_hours = 4  # Intervalle entre les analyses (4 heures)
        self.is_running = False
        
    def initialize(self):
        """Initialise le worker"""
        try:
            logger.info("🚀 Initialisation du Background Worker...")
            
            # Vérifier les variables d'environnement
            required_vars = ['SCRAPINGBEE_API_KEY', 'OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                raise Exception(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
            
            # Initialiser le scraper
            self.scraper.initialize_sync()
            logger.info("✅ Scraper initialisé avec succès")
            
            # Vérifier la connexion à la base de données
            if not self.db.is_connected():
                raise Exception("Impossible de se connecter à la base de données")
            logger.info("✅ Connexion à la base de données établie")
            
            self.is_running = True
            logger.info(f"✅ Background Worker prêt - Intervalle: {self.interval_hours} heures")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {e}")
            raise
    
    async def run_market_analysis(self):
        """Exécute une analyse de marché complète et la sauvegarde"""
        start_time = time.time()
        
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
                
                # Sauvegarder l'erreur dans la base de données
                error_analysis = MarketAnalysis(
                    analysis_type='automatic',
                    worker_status='error',
                    error_message=result['error'],
                    processing_time_seconds=int(time.time() - start_time)
                )
                self.db.save_analysis(error_analysis)
                return False
            else:
                logger.info("✅ Analyse terminée avec succès")
                
                # Créer l'objet d'analyse pour la base de données
                analysis = MarketAnalysis(
                    analysis_type='automatic',
                    summary=result.get('summary'),
                    key_points=result.get('key_points', []),
                    structured_data=result.get('structured_data', {}),
                    insights=result.get('insights', []),
                    risks=result.get('risks', []),
                    opportunities=result.get('opportunities', []),
                    sources=result.get('sources', []),
                    confidence_score=result.get('confidence_score', 0.0),
                    worker_status='completed',
                    processing_time_seconds=int(time.time() - start_time)
                )
                
                # Sauvegarder dans la base de données
                analysis_id = self.db.save_analysis(analysis)
                
                if analysis_id:
                    logger.info(f"💾 Analyse sauvegardée avec l'ID: {analysis_id}")
                else:
                    logger.error("❌ Erreur lors de la sauvegarde de l'analyse")
                
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
                    'confidence': result.get('confidence_score', 0),
                    'processing_time': int(time.time() - start_time)
                }
                
                logger.info(f"📊 Statistiques: {stats}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de l'analyse: {e}")
            
            # Sauvegarder l'erreur dans la base de données
            error_analysis = MarketAnalysis(
                analysis_type='automatic',
                worker_status='error',
                error_message=str(e),
                processing_time_seconds=int(time.time() - start_time)
            )
            self.db.save_analysis(error_analysis)
            return False

    async def run_continuous_loop(self):
        """Boucle principale du worker"""
        logger.info("🔄 Démarrage de la boucle continue...")
        
        while self.is_running:
            try:
                logger.info("⏰ Déclenchement de l'analyse automatique...")
                
                # Exécuter l'analyse
                success = await self.run_market_analysis()
                
                if success:
                    logger.info("✅ Analyse automatique terminée avec succès")
                else:
                    logger.warning("⚠️ Analyse automatique échouée")
                
                # Attendre l'intervalle suivant
                logger.info(f"⏳ Attente de {self.interval_hours} heures avant la prochaine analyse...")
                await asyncio.sleep(self.interval_hours * 3600)  # Convertir en secondes
                
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle continue: {e}")
                logger.info("⏳ Attente de 1 heure avant de réessayer...")
                await asyncio.sleep(3600)  # Attendre 1 heure en cas d'erreur
    
    def stop(self):
        """Arrête le worker"""
        logger.info("🛑 Arrêt du Background Worker...")
        self.is_running = False
        
        # Nettoyer le scraper
        if hasattr(self.scraper, 'cleanup'):
            self.scraper.cleanup()

async def main():
    """Fonction principale"""
    worker = MarketAnalysisWorker()
    
    try:
        # Initialiser le worker
        worker.initialize()
        
        # Démarrer la boucle continue
        await worker.run_continuous_loop()
        
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
    finally:
        worker.stop()

if __name__ == "__main__":
    # Démarrer la boucle d'événements asyncio
    asyncio.run(main()) 