#!/usr/bin/env python3
"""
Test local avec les vraies clés API
Alpha Vantage: XCRQGI1OMS5381DE
EODHD: 687ae6e8493e52.65071366
Finnhub: d1tbknpr01qr2iithm20d1tbknpr01qr2iithm2g
"""

import os
import sys
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_environment_keys():
    """Configure les clés API dans l'environnement"""
    os.environ['ALPHA_VANTAGE_KEY'] = 'XCRQGI1OMS5381DE'
    os.environ['EODHD_KEY'] = '687ae6e8493e52.65071366'
    os.environ['FINNHUB_KEY'] = 'd1tbknpr01qr2iithm20d1tbknpr01qr2iithm2g'
    
    logger.info("✅ Clés API configurées:")
    logger.info(f"   Alpha Vantage: {os.environ['ALPHA_VANTAGE_KEY'][:4]}...")
    logger.info(f"   EODHD: {os.environ['EODHD_KEY'][:4]}...")
    logger.info(f"   Finnhub: {os.environ['FINNHUB_KEY'][:4]}...")

def test_individual_apis():
    """Test des APIs individuelles avec les vraies clés"""
    try:
        logger.info("🧪 Test des APIs individuelles avec vraies clés")
        
        from stock_api_manager import AlphaVantageAPI, EODHDAPI, FinnhubAPI
        
        symbol = "AAPL"
        
        # Test Alpha Vantage
        try:
            logger.info(f"📞 Test Alpha Vantage pour {symbol}")
            alpha_vantage = AlphaVantageAPI()
            result = alpha_vantage.get_stock_price(symbol)
            
            if result and result.get('price', 0) > 0:
                logger.info(f"   ✅ Alpha Vantage: {result['price']} USD")
                logger.info(f"   📈 Change: {result.get('change_percent', 'N/A')}%")
                logger.info(f"   📊 Volume: {result.get('volume', 'N/A')}")
            else:
                logger.warning(f"   ⚠️ Alpha Vantage: pas de données")
        except Exception as e:
            logger.error(f"   ❌ Alpha Vantage: {e}")
        
        # Test EODHD
        try:
            logger.info(f"📞 Test EODHD pour {symbol}")
            eodhd = EODHDAPI()
            result = eodhd.get_stock_price(symbol)
            
            if result and result.get('price', 0) > 0:
                logger.info(f"   ✅ EODHD: {result['price']} {result.get('currency', 'USD')}")
                logger.info(f"   📈 Change: {result.get('change_percent', 'N/A')}%")
                logger.info(f"   📊 Volume: {result.get('volume', 'N/A')}")
            else:
                logger.warning(f"   ⚠️ EODHD: pas de données")
        except Exception as e:
            logger.error(f"   ❌ EODHD: {e}")
        
        # Test Finnhub
        try:
            logger.info(f"📞 Test Finnhub pour {symbol}")
            finnhub = FinnhubAPI()
            result = finnhub.get_stock_price(symbol)
            
            if result and result.get('price', 0) > 0:
                logger.info(f"   ✅ Finnhub: {result['price']} USD")
                logger.info(f"   📈 Change: {result.get('change_percent', 'N/A')}%")
                logger.info(f"   📊 Volume: {result.get('volume', 'N/A')}")
            else:
                logger.warning(f"   ⚠️ Finnhub: pas de données")
        except Exception as e:
            logger.error(f"   ❌ Finnhub: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test APIs individuelles: {e}")
        return False

def test_sequential_fallback():
    """Test du fallback séquentiel"""
    try:
        logger.info("🧪 Test du fallback séquentiel")
        
        from stock_api_manager import stock_api_manager
        
        symbols = ["AAPL", "TSLA", "MSFT", "IREN.SW"]
        
        for symbol in symbols:
            try:
                logger.info(f"📞 Test séquentiel pour {symbol}")
                result = stock_api_manager.get_stock_price(symbol)
                
                if result and result.get('price', 0) > 0:
                    logger.info(f"   ✅ Prix: {result['price']} {result.get('currency', 'USD')}")
                    logger.info(f"   📊 Source: {result.get('source', 'N/A')}")
                    logger.info(f"   📈 Change: {result.get('change_percent', 'N/A')}%")
                else:
                    logger.error(f"   ❌ Pas de données pour {symbol}")
                    
                # Attendre entre les tests
                time.sleep(3)
                    
            except Exception as e:
                logger.error(f"   ❌ Erreur pour {symbol}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test séquentiel: {e}")
        return False

def test_cache_functionality():
    """Test de la fonctionnalité de cache"""
    try:
        logger.info("🧪 Test de la fonctionnalité de cache")
        
        from stock_api_manager import stock_api_manager
        
        symbol = "AAPL"
        
        # Premier appel (pas de cache)
        logger.info(f"📞 Premier appel pour {symbol}")
        start_time = time.time()
        result1 = stock_api_manager.get_stock_price(symbol)
        time1 = time.time() - start_time
        
        if result1:
            logger.info(f"   ✅ Premier appel: {result1['price']} USD en {time1:.2f}s")
        
        # Deuxième appel (avec cache)
        logger.info(f"📞 Deuxième appel pour {symbol} (cache)")
        start_time = time.time()
        result2 = stock_api_manager.get_stock_price(symbol)
        time2 = time.time() - start_time
        
        if result2:
            logger.info(f"   ✅ Deuxième appel: {result2['price']} USD en {time2:.2f}s")
        
        # Vérifier le statut du cache
        cache_status = stock_api_manager.get_cache_status()
        logger.info(f"   📊 Cache status: {cache_status}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test cache: {e}")
        return False

def test_health_status():
    """Test du statut de santé"""
    try:
        logger.info("🧪 Test du statut de santé")
        
        from stock_api_manager import stock_api_manager
        
        health = stock_api_manager.get_health_status()
        
        logger.info("📊 Statut de santé:")
        logger.info(f"   Alpha Vantage: {health.get('alpha_vantage', {})}")
        logger.info(f"   EODHD: {health.get('eodhd', {})}")
        logger.info(f"   Finnhub: {health.get('finnhub', {})}")
        logger.info(f"   Cache: {health.get('cache', {})}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test santé: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 Test local avec vraies clés API")
    
    # Configurer les clés
    setup_environment_keys()
    
    # Test 1: APIs individuelles
    logger.info("\n" + "="*50)
    test_individual_apis()
    
    # Test 2: Fallback séquentiel
    logger.info("\n" + "="*50)
    test_sequential_fallback()
    
    # Test 3: Cache
    logger.info("\n" + "="*50)
    test_cache_functionality()
    
    # Test 4: Santé
    logger.info("\n" + "="*50)
    test_health_status()
    
    logger.info("\n" + "="*50)
    logger.info("📋 TESTS TERMINÉS")

if __name__ == "__main__":
    main() 