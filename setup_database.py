#!/usr/bin/env python3
"""
Script de configuration de la base de données pour le Background Worker
"""

import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Configure la base de données pour le Background Worker"""
    try:
        logger.info("🔧 Configuration de la base de données...")
        
        # Vérifier les variables d'environnement
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("❌ Variables d'environnement Supabase manquantes")
            logger.info("📋 Variables requises:")
            logger.info("   - SUPABASE_URL")
            logger.info("   - SUPABASE_KEY")
            return False
        
        logger.info("✅ Variables d'environnement Supabase trouvées")
        
        # Lire le script SQL
        try:
            with open('create_market_analyses_table.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
            logger.info("✅ Script SQL lu avec succès")
        except FileNotFoundError:
            logger.error("❌ Fichier create_market_analyses_table.sql non trouvé")
            return False
        
        # Instructions pour l'utilisateur
        logger.info("\n📋 Instructions pour configurer la base de données:")
        logger.info("1. Allez sur votre dashboard Supabase")
        logger.info("2. Ouvrez l'éditeur SQL")
        logger.info("3. Copiez-collez le contenu du fichier create_market_analyses_table.sql")
        logger.info("4. Exécutez le script")
        logger.info("\n📄 Contenu du script SQL:")
        logger.info("-" * 50)
        print(sql_script)
        logger.info("-" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la configuration: {e}")
        return False

def test_connection():
    """Test de connexion à Supabase"""
    try:
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        
        if db.is_connected():
            logger.info("✅ Connexion à Supabase réussie")
            return True
        else:
            logger.error("❌ Échec de la connexion à Supabase")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur de connexion: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 Configuration de la base de données pour le Background Worker")
    logger.info("=" * 60)
    
    # Test de connexion
    logger.info("📋 Test de connexion à Supabase...")
    if not test_connection():
        logger.error("❌ Impossible de se connecter à Supabase")
        logger.info("💡 Vérifiez vos variables d'environnement SUPABASE_URL et SUPABASE_KEY")
        return False
    
    # Configuration de la base de données
    logger.info("\n📋 Configuration de la base de données...")
    if not setup_database():
        logger.error("❌ Échec de la configuration")
        return False
    
    logger.info("\n✅ Configuration terminée")
    logger.info("📋 Prochaines étapes:")
    logger.info("1. Exécutez le script SQL dans Supabase")
    logger.info("2. Redéployez le Background Worker")
    logger.info("3. Testez l'intégration")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 