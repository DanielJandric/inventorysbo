#!/usr/bin/env python3
"""
Test du wrapper de stabilisation Manus adapté à l'environnement InventorySBO
"""

import sys
import os
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_stable_api_basic():
    """Test basique de l'API stabilisée"""
    try:
        from stable_manus_wrapper import stable_manus_api
        
        logger.info("🧪 Test basique de l'API stabilisée")
        
        # Test avec un symbole
        symbol = "AAPL"
        start_time = time.time()
        
        result = stable_manus_api.get_stock_price(symbol)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"⏱️ Durée: {duration:.2f}s")
        logger.info(f"📊 Status: {result.get('status', 'N/A')}")
        logger.info(f"💰 Prix: {result.get('price', 'N/A')} {result.get('currency', 'N/A')}")
        logger.info(f"📈 Changement: {result.get('change_percent', 'N/A')}%")
        logger.info(f"📦 Source: {result.get('source', 'N/A')}")
        
        if result.get('price', 0) > 0:
            logger.info("✅ Test basique réussi")
            return True
        else:
            logger.error("❌ Test basique échoué")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test basique: {e}")
        return False

def test_multiple_symbols():
    """Test avec plusieurs symboles"""
    try:
        from stable_manus_wrapper import stable_manus_api
        
        logger.info("🧪 Test avec plusieurs symboles")
        
        symbols = ["AAPL", "TSLA", "MSFT", "IREN.SW"]
        results = {}
        
        start_time = time.time()
        
        for symbol in symbols:
            logger.info(f"📞 Récupération pour {symbol}")
            result = stable_manus_api.get_stock_price(symbol)
            results[symbol] = result
            
            if result.get('price', 0) > 0:
                logger.info(f"✅ {symbol}: {result['price']} {result['currency']}")
            else:
                logger.warning(f"⚠️ {symbol}: échec")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        success_count = sum(1 for r in results.values() if r.get('price', 0) > 0)
        
        logger.info(f"📊 Résultats: {success_count}/{len(symbols)} succès")
        logger.info(f"⏱️ Durée totale: {total_duration:.2f}s")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Erreur test multiple: {e}")
        return False

def test_circuit_breaker():
    """Test du circuit breaker"""
    try:
        from stable_manus_wrapper import stable_manus_api
        
        logger.info("🧪 Test du circuit breaker")
        
        # Vérifier l'état initial
        health = stable_manus_api.get_health_status()
        circuit_state = health['circuit_breaker']['state']
        
        logger.info(f"🔌 État initial du circuit: {circuit_state}")
        
        # Faire quelques appels pour tester
        for i in range(3):
            try:
                result = stable_manus_api.get_stock_price("AAPL")
                logger.info(f"✅ Appel {i+1}: succès")
            except Exception as e:
                logger.warning(f"⚠️ Appel {i+1}: échec - {e}")
        
        # Vérifier l'état final
        health = stable_manus_api.get_health_status()
        final_state = health['circuit_breaker']['state']
        failure_count = health['circuit_breaker']['failure_count']
        
        logger.info(f"🔌 État final du circuit: {final_state}")
        logger.info(f"📊 Nombre d'échecs: {failure_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test circuit breaker: {e}")
        return False

def test_health_monitoring():
    """Test du monitoring de santé"""
    try:
        from stable_manus_wrapper import stable_manus_api
        
        logger.info("🧪 Test du monitoring de santé")
        
        # Faire quelques appels pour générer des métriques
        for symbol in ["AAPL", "TSLA"]:
            try:
                stable_manus_api.get_stock_price(symbol)
            except:
                pass
        
        # Obtenir le statut de santé
        health = stable_manus_api.get_health_status()
        
        logger.info("📊 Métriques de santé:")
        logger.info(f"   Taux de succès: {health['api_health']['success_rate']:.2%}")
        logger.info(f"   Temps de réponse moyen: {health['api_health']['avg_response_time']:.2f}s")
        logger.info(f"   Total requêtes: {health['api_health']['total_requests']}")
        logger.info(f"   Requêtes réussies: {health['api_health']['successful_requests']}")
        
        # Vérifier la santé
        is_healthy = health['api_health']['healthy']
        logger.info(f"🏥 Santé globale: {'✅ Bonne' if is_healthy else '❌ Dégradée'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test monitoring: {e}")
        return False

def test_cache_functionality():
    """Test de la fonctionnalité de cache"""
    try:
        from stable_manus_wrapper import stable_manus_api
        
        logger.info("🧪 Test de la fonctionnalité de cache")
        
        symbol = "AAPL"
        
        # Premier appel (pas de cache)
        start_time = time.time()
        result1 = stable_manus_api.get_stock_price(symbol)
        time1 = time.time() - start_time
        
        # Deuxième appel (avec cache)
        start_time = time.time()
        result2 = stable_manus_api.get_stock_price(symbol)
        time2 = time.time() - start_time
        
        logger.info(f"⏱️ Premier appel: {time1:.3f}s")
        logger.info(f"⏱️ Deuxième appel: {time2:.3f}s")
        
        if time2 < time1 * 0.5:  # Le deuxième appel devrait être plus rapide
            logger.info("✅ Cache fonctionne correctement")
            return True
        else:
            logger.warning("⚠️ Cache ne semble pas fonctionner")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur test cache: {e}")
        return False

def test_compatibility_functions():
    """Test des fonctions de compatibilité"""
    try:
        from stable_manus_wrapper import get_stock_price_stable, get_health_status_stable
        
        logger.info("🧪 Test des fonctions de compatibilité")
        
        # Test de la fonction de compatibilité
        result = get_stock_price_stable("AAPL")
        
        if result and result.get('price', 0) > 0:
            logger.info("✅ Fonction de compatibilité fonctionne")
            
            # Test du statut de santé
            health = get_health_status_stable()
            logger.info("✅ Statut de santé accessible")
            
            return True
        else:
            logger.error("❌ Fonction de compatibilité échouée")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur test compatibilité: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Début des tests du wrapper de stabilisation")
    
    # Test 1: API basique
    logger.info("\n" + "="*50)
    success1 = test_stable_api_basic()
    
    # Test 2: Plusieurs symboles
    logger.info("\n" + "="*50)
    success2 = test_multiple_symbols()
    
    # Test 3: Circuit breaker
    logger.info("\n" + "="*50)
    success3 = test_circuit_breaker()
    
    # Test 4: Monitoring de santé
    logger.info("\n" + "="*50)
    success4 = test_health_monitoring()
    
    # Test 5: Cache
    logger.info("\n" + "="*50)
    success5 = test_cache_functionality()
    
    # Test 6: Compatibilité
    logger.info("\n" + "="*50)
    success6 = test_compatibility_functions()
    
    # Résumé
    logger.info("\n" + "="*50)
    logger.info("📋 RÉSUMÉ DES TESTS")
    logger.info(f"✅ API basique: {'SUCCÈS' if success1 else 'ÉCHEC'}")
    logger.info(f"✅ Plusieurs symboles: {'SUCCÈS' if success2 else 'ÉCHEC'}")
    logger.info(f"✅ Circuit breaker: {'SUCCÈS' if success3 else 'ÉCHEC'}")
    logger.info(f"✅ Monitoring: {'SUCCÈS' if success4 else 'ÉCHEC'}")
    logger.info(f"✅ Cache: {'SUCCÈS' if success5 else 'ÉCHEC'}")
    logger.info(f"✅ Compatibilité: {'SUCCÈS' if success6 else 'ÉCHEC'}")
    
    if all([success1, success2, success3, success4, success5, success6]):
        logger.info("🎉 Tous les tests réussis!")
        logger.info("🚀 Wrapper de stabilisation prêt pour la production!")
        return True
    else:
        logger.error("❌ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 