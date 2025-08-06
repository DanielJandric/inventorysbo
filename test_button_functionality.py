#!/usr/bin/env python3
"""
Test de la fonctionnalité du bouton triggerBackgroundWorker
"""

import requests
import json
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_button_functionality():
    """Test de la fonctionnalité du bouton"""
    try:
        logger.info("🧪 Test de la fonctionnalité du bouton triggerBackgroundWorker...")
        
        # URL de l'application
        base_url = "https://inventorysbo.onrender.com"
        
        # Test 1: Vérifier que l'endpoint fonctionne
        logger.info("📋 Test 1: Vérification de l'endpoint /api/background-worker/trigger")
        trigger_url = f"{base_url}/api/background-worker/trigger"
        
        response = requests.post(trigger_url, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Endpoint fonctionne: {data}")
            
            if data.get('success'):
                logger.info("✅ Déclenchement réussi")
                return True
            else:
                logger.error(f"❌ Erreur dans la réponse: {data}")
                return False
        else:
            logger.error(f"❌ Erreur HTTP: {response.status_code}")
            logger.error(f"Réponse: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

def test_ui_accessibility():
    """Test de l'accessibilité de l'interface utilisateur"""
    try:
        logger.info("📋 Test 2: Vérification de l'accessibilité de l'interface")
        
        base_url = "https://inventorysbo.onrender.com"
        markets_url = f"{base_url}/markets"
        
        response = requests.get(markets_url)
        
        if response.status_code == 200:
            logger.info("✅ Page /markets accessible")
            
            # Vérifier si le bouton est présent dans le HTML
            if 'triggerBackgroundWorker' in response.text:
                logger.info("✅ Bouton triggerBackgroundWorker présent dans le HTML")
                return True
            else:
                logger.error("❌ Bouton triggerBackgroundWorker non trouvé dans le HTML")
                return False
        else:
            logger.error(f"❌ Page /markets non accessible: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test UI: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 Test de la fonctionnalité du bouton triggerBackgroundWorker")
    logger.info("=" * 60)
    
    # Test 1: Fonctionnalité de l'endpoint
    success1 = test_button_functionality()
    
    # Test 2: Accessibilité de l'interface
    success2 = test_ui_accessibility()
    
    logger.info("\n" + "=" * 60)
    if success1 and success2:
        logger.info("✅ Tous les tests réussis ! Le bouton devrait fonctionner.")
        logger.info("💡 Instructions pour tester:")
        logger.info("1. Allez sur https://inventorysbo.onrender.com/markets")
        logger.info("2. Cliquez sur le bouton 'Déclencher Worker'")
        logger.info("3. Vérifiez que l'analyse ScrapingBee se lance")
    else:
        logger.error("❌ Certains tests ont échoué")
        if not success1:
            logger.error("   - L'endpoint /api/background-worker/trigger ne fonctionne pas")
        if not success2:
            logger.error("   - L'interface utilisateur n'est pas accessible")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 