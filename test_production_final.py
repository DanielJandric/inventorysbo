#!/usr/bin/env python3
"""
Test final de la production après déploiement
"""

import requests
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_production_api():
    """Test de l'API en production"""
    try:
        logger.info("🧪 Test de l'API en production")
        
        # URL de production
        production_url = "https://inventorysbo.onrender.com"
        
        # Test 1: Endpoint de base
        try:
            response = requests.get(f"{production_url}/", timeout=10)
            logger.info(f"✅ App accessible: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ App non accessible: {e}")
            return False
        
        # Test 2: API stock price
        symbols = ["AAPL", "TSLA", "MSFT", "IREN.SW"]
        
        for symbol in symbols:
            try:
                logger.info(f"📞 Test prix pour {symbol}")
                response = requests.get(f"{production_url}/api/stock-price/{symbol}", timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        stock_data = data.get('data', {})
                        price = stock_data.get('price', 0)
                        source = stock_data.get('source', 'N/A')
                        
                        logger.info(f"   Prix: {price}")
                        logger.info(f"   Source: {source}")
                        
                        if price > 0:
                            logger.info(f"   ✅ Prix correct pour {symbol}")
                        else:
                            logger.error(f"   ❌ Prix invalide pour {symbol}")
                    else:
                        logger.error(f"   ❌ API error: {data.get('error')}")
                else:
                    logger.error(f"   ❌ HTTP {response.status_code}")
                    
                # Attendre entre les tests
                time.sleep(2)
                    
            except Exception as e:
                logger.error(f"   ❌ Erreur pour {symbol}: {e}")
        
        # Test 3: Cache status
        try:
            logger.info("📊 Test cache status")
            response = requests.get(f"{production_url}/api/stock-price/cache/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   Cache: {data.get('cache', {})}")
                logger.info(f"   Health: {data.get('health', {})}")
                logger.info(f"   APIs: {data.get('apis', [])}")
            else:
                logger.error(f"   ❌ Cache status HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"   ❌ Erreur cache status: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test production: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 Test final de la production")
    
    # Attendre que le déploiement soit terminé
    logger.info("⏳ Attente du déploiement (30s)...")
    time.sleep(30)
    
    # Test production
    test_production_api()
    
    logger.info("📋 TEST TERMINÉ")

if __name__ == "__main__":
    main() 