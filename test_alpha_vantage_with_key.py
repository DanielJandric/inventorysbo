#!/usr/bin/env python3
"""
Test Alpha Vantage avec la nouvelle clé et rate limiting
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

def test_alpha_vantage_single():
    """Test d'un seul appel Alpha Vantage"""
    try:
        from alpha_vantage_fallback import alpha_vantage_fallback
        
        logger.info("🧪 Test Alpha Vantage - appel unique")
        start_time = time.time()
        
        result = alpha_vantage_fallback.get_stock_price("AAPL")
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result:
            logger.info(f"✅ Alpha Vantage réussi pour AAPL:")
            logger.info(f"   Prix: {result['price']} {result['currency']}")
            logger.info(f"   Changement: {result['change']} ({result['change_percent']}%)")
            logger.info(f"   Volume: {result['volume']}")
            logger.info(f"   Durée: {duration:.2f}s")
            return True
        else:
            logger.error("❌ Alpha Vantage échoué pour AAPL")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test Alpha Vantage: {e}")
        return False

def test_alpha_vantage_multiple():
    """Test de plusieurs appels Alpha Vantage avec rate limiting"""
    try:
        from alpha_vantage_fallback import alpha_vantage_fallback
        
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL", "IREN.SW"]
        results = []
        
        logger.info("🧪 Test Alpha Vantage - appels multiples avec rate limiting")
        start_time = time.time()
        
        for i, symbol in enumerate(symbols):
            logger.info(f"📞 Appel {i+1}/{len(symbols)} pour {symbol}")
            result = alpha_vantage_fallback.get_stock_price(symbol)
            
            if result:
                logger.info(f"✅ {symbol}: {result['price']} {result['currency']}")
                results.append(result)
            else:
                logger.warning(f"⚠️ {symbol}: échec")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        logger.info(f"📊 Résultats: {len(results)}/{len(symbols)} succès")
        logger.info(f"⏱️ Durée totale: {total_duration:.2f}s")
        logger.info(f"📈 Temps moyen par appel: {total_duration/len(symbols):.2f}s")
        
        return len(results) > 0
        
    except Exception as e:
        logger.error(f"❌ Erreur test multiple Alpha Vantage: {e}")
        return False

def test_rate_limiting():
    """Test spécifique du rate limiting"""
    try:
        from alpha_vantage_fallback import alpha_vantage_fallback
        
        logger.info("🧪 Test rate limiting Alpha Vantage")
        
        # Premier appel
        start_time = time.time()
        result1 = alpha_vantage_fallback.get_stock_price("AAPL")
        time1 = time.time() - start_time
        
        # Deuxième appel immédiat (devrait être rate limité)
        start_time = time.time()
        result2 = alpha_vantage_fallback.get_stock_price("TSLA")
        time2 = time.time() - start_time
        
        logger.info(f"⏱️ Premier appel: {time1:.2f}s")
        logger.info(f"⏱️ Deuxième appel: {time2:.2f}s")
        
        if time2 > 10:  # Le deuxième appel devrait prendre plus de 10s (rate limiting)
            logger.info("✅ Rate limiting fonctionne correctement")
            return True
        else:
            logger.warning("⚠️ Rate limiting ne semble pas fonctionner")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test rate limiting: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Début des tests Alpha Vantage avec nouvelle clé")
    
    # Test 1: Appel unique
    logger.info("\n" + "="*50)
    success1 = test_alpha_vantage_single()
    
    # Test 2: Rate limiting
    logger.info("\n" + "="*50)
    success2 = test_rate_limiting()
    
    # Test 3: Appels multiples
    logger.info("\n" + "="*50)
    success3 = test_alpha_vantage_multiple()
    
    # Résumé
    logger.info("\n" + "="*50)
    logger.info("📋 RÉSUMÉ DES TESTS")
    logger.info(f"✅ Appel unique: {'SUCCÈS' if success1 else 'ÉCHEC'}")
    logger.info(f"✅ Rate limiting: {'SUCCÈS' if success2 else 'ÉCHEC'}")
    logger.info(f"✅ Appels multiples: {'SUCCÈS' if success3 else 'ÉCHEC'}")
    
    if success1 and success2 and success3:
        logger.info("🎉 Tous les tests Alpha Vantage réussis!")
        return True
    else:
        logger.error("❌ Certains tests Alpha Vantage ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 