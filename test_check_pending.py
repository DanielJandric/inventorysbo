#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier les tâches en attente dans la base de données.
"""

import os
import logging
from dotenv import load_dotenv
from market_analysis_db import get_market_analysis_db, MarketAnalysis

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_pending_tasks():
    """Vérifie et affiche les tâches en attente."""
    logger.info("🔍 Connexion à la base de données pour vérifier les tâches en attente...")
    
    db = get_market_analysis_db()

    if not db.is_connected():
        logger.error("❌ Impossible de se connecter à la base de données. Vérifiez vos variables d'environnement SUPABASE_URL et SUPABASE_KEY.")
        return

    try:
        pending_task = db.get_pending_analysis()

        if pending_task:
            logger.info("✅ TÂCHE EN ATTENTE TROUVÉE !")
            logger.info("=" * 40)
            logger.info(f"  ID: {pending_task.id}")
            logger.info(f"  Statut: {pending_task.worker_status}")
            logger.info(f"  Type: {pending_task.analysis_type}")
            logger.info(f"  Créée le: {pending_task.created_at}")
            logger.info(f"  Prompt: {pending_task.prompt[:100]}...")
            logger.info("=" * 40)
            logger.info("➡️ Le problème vient probablement du Background Worker qui ne traite pas la tâche.")
        else:
            logger.warning("🟡 AUCUNE TÂCHE EN ATTENTE TROUVÉE.")
            logger.info("=" * 40)
            logger.info("➡️ Le problème vient probablement de l'application web qui ne crée pas la tâche lorsque vous cliquez sur le bouton.")
            logger.info("   Assurez-vous d'avoir cliqué sur 'Lancer une Nouvelle Analyse' avant de lancer ce script.")

    except Exception as e:
        logger.error(f"❌ Une erreur est survenue lors de la vérification: {e}")

if __name__ == "__main__":
    check_pending_tasks()
