#!/usr/bin/env python3
"""
Test d'intégration de la base de données pour le Background Worker
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test de la connexion à la base de données"""
    try:
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        
        if db.is_connected():
            logger.info("✅ Connexion à la base de données réussie")
            return True
        else:
            logger.error("❌ Échec de la connexion à la base de données")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de connexion: {e}")
        return False

def test_create_analysis():
    """Test de création d'une analyse"""
    try:
        from market_analysis_db import get_market_analysis_db, MarketAnalysis
        db = get_market_analysis_db()
        
        # Créer une analyse de test
        test_analysis = MarketAnalysis(
            analysis_type='test',
            summary='Test d\'intégration de la base de données',
            key_points=[
                'Connexion à Supabase réussie',
                'Sauvegarde des analyses fonctionnelle',
                'Récupération des données opérationnelle'
            ],
            structured_data={
                'prix': 'Test',
                'tendance': 'Positive',
                'volumes': 'Élevés'
            },
            insights=['Test réussi'],
            risks=['Aucun risque'],
            opportunities=['Intégration complète'],
            sources=[{'title': 'Test Integration', 'url': '#'}],
            confidence_score=0.95,
            worker_status='completed'
        )
        
        # Sauvegarder l'analyse
        analysis_id = db.save_analysis(test_analysis)
        
        if analysis_id:
            logger.info(f"✅ Analyse de test créée avec l'ID: {analysis_id}")
            return analysis_id
        else:
            logger.error("❌ Échec de la création de l'analyse")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de création: {e}")
        return None

def test_retrieve_analysis(analysis_id=None):
    """Test de récupération d'analyses"""
    try:
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        
        # Récupérer la dernière analyse
        latest = db.get_latest_analysis()
        
        if latest:
            logger.info(f"✅ Dernière analyse récupérée (ID: {latest.id})")
            logger.info(f"   Type: {latest.analysis_type}")
            logger.info(f"   Timestamp: {latest.timestamp}")
            logger.info(f"   Résumé: {latest.summary[:100]}...")
            return True
        else:
            logger.warning("⚠️ Aucune analyse trouvée")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de récupération: {e}")
        return False

def test_worker_status():
    """Test du statut du worker"""
    try:
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        
        status = db.get_worker_status()
        
        logger.info("📊 Statut du Background Worker:")
        logger.info(f"   Disponible: {status.get('available', False)}")
        logger.info(f"   Statut: {status.get('status', 'unknown')}")
        logger.info(f"   Dernière vérification: {status.get('last_check', 'N/A')}")
        
        if 'last_analysis' in status:
            logger.info(f"   Dernière analyse: {status['last_analysis']}")
            logger.info(f"   Heures depuis analyse: {status.get('hours_since_analysis', 'N/A')}")
        
        return status.get('available', False)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de statut: {e}")
        return False

def test_app_integration():
    """Test de l'intégration avec l'application web"""
    try:
        # Importer les fonctions de l'app
        sys.path.append('.')
        from app import check_background_worker_status, get_latest_market_analysis
        
        # Test du statut
        status = check_background_worker_status()
        logger.info("✅ Test d'intégration app - Statut:")
        logger.info(f"   {status}")
        
        # Test de récupération d'analyse
        analysis = get_latest_market_analysis()
        if analysis:
            logger.info("✅ Test d'intégration app - Analyse récupérée")
            logger.info(f"   Timestamp: {analysis.get('timestamp')}")
        else:
            logger.info("ℹ️ Test d'intégration app - Aucune analyse disponible")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test d'intégration app: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🧪 Démarrage des tests d'intégration de la base de données")
    logger.info("=" * 60)
    
    # Test 1: Connexion à la base de données
    logger.info("📋 Test 1: Connexion à la base de données")
    if not test_database_connection():
        logger.error("❌ Test de connexion échoué - Arrêt des tests")
        return False
    
    # Test 2: Création d'une analyse
    logger.info("\n📋 Test 2: Création d'une analyse")
    analysis_id = test_create_analysis()
    
    # Test 3: Récupération d'analyses
    logger.info("\n📋 Test 3: Récupération d'analyses")
    test_retrieve_analysis(analysis_id)
    
    # Test 4: Statut du worker
    logger.info("\n📋 Test 4: Statut du Background Worker")
    test_worker_status()
    
    # Test 5: Intégration avec l'app
    logger.info("\n📋 Test 5: Intégration avec l'application web")
    test_app_integration()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Tests d'intégration terminés")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 