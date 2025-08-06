#!/usr/bin/env python3
"""
Test du déclenchement du Background Worker depuis l'application web
"""

import requests
import json
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_worker_trigger():
    """Test du déclenchement du Background Worker"""
    try:
        logger.info("🧪 Test du déclenchement du Background Worker...")
        
        # URL de l'application (remplacez par votre URL de production)
        base_url = "https://inventorysbo.onrender.com"
        
        # Test 1: Déclencher le worker
        logger.info("📋 Test 1: Déclenchement du Background Worker")
        trigger_url = f"{base_url}/api/background-worker/trigger"
        
        response = requests.post(trigger_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Déclenchement réussi")
            logger.info(f"   Message: {data.get('message', 'N/A')}")
            logger.info(f"   Timestamp: {data.get('timestamp', 'N/A')}")
        else:
            logger.error(f"❌ Erreur déclenchement: {response.status_code}")
            logger.error(f"   Réponse: {response.text}")
            return False
        
        # Test 2: Vérifier le statut après quelques secondes
        logger.info("📋 Test 2: Vérification du statut")
        time.sleep(5)  # Attendre un peu
        
        status_url = f"{base_url}/api/background-worker/status"
        response = requests.get(status_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Statut récupéré")
            logger.info(f"   Status: {data.get('status', {})}")
        else:
            logger.error(f"❌ Erreur statut: {response.status_code}")
            logger.error(f"   Réponse: {response.text}")
        
        # Test 3: Récupérer la dernière analyse
        logger.info("📋 Test 3: Récupération de la dernière analyse")
        time.sleep(10)  # Attendre plus longtemps pour l'analyse
        
        analysis_url = f"{base_url}/api/scrapingbee/market-update/quick"
        response = requests.post(analysis_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Analyse récupérée")
            logger.info(f"   Source: {data.get('source', 'N/A')}")
            logger.info(f"   Type: {data.get('analysis_type', 'N/A')}")
            
            if 'data' in data and 'summary' in data['data']:
                summary = data['data']['summary']
                logger.info(f"   Résumé: {summary[:100]}...")
            else:
                logger.warning("⚠️ Pas de résumé dans l'analyse")
                
        elif response.status_code == 404:
            logger.info("ℹ️ Aucune analyse disponible (normal si l'analyse est encore en cours)")
        else:
            logger.error(f"❌ Erreur récupération analyse: {response.status_code}")
            logger.error(f"   Réponse: {response.text}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

def test_local_trigger():
    """Test local du déclenchement (si l'app tourne en local)"""
    try:
        logger.info("🧪 Test local du déclenchement...")
        
        # URL locale
        base_url = "http://localhost:5000"
        
        # Test du déclenchement
        trigger_url = f"{base_url}/api/background-worker/trigger"
        
        response = requests.post(trigger_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Déclenchement local réussi")
            logger.info(f"   Message: {data.get('message', 'N/A')}")
            return True
        else:
            logger.error(f"❌ Erreur déclenchement local: {response.status_code}")
            logger.error(f"   Réponse: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test local: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 Test du déclenchement du Background Worker")
    logger.info("=" * 60)
    
    # Test de production
    logger.info("📋 Test de production (Render)")
    success_prod = test_worker_trigger()
    
    logger.info("\n" + "=" * 60)
    
    # Test local (optionnel)
    logger.info("📋 Test local (si l'app tourne en local)")
    try:
        success_local = test_local_trigger()
    except:
        logger.info("ℹ️ Test local ignoré (app non disponible en local)")
        success_local = False
    
    # Résumé
    logger.info("\n" + "=" * 60)
    logger.info("📊 RÉSUMÉ DES TESTS:")
    logger.info(f"   Production: {'✅' if success_prod else '❌'}")
    logger.info(f"   Local: {'✅' if success_local else '❌'}")
    
    if success_prod or success_local:
        logger.info("🎉 Au moins un test a réussi!")
    else:
        logger.error("❌ Tous les tests ont échoué")

if __name__ == "__main__":
    main() 