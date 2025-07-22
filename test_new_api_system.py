#!/usr/bin/env python3
"""
Test du nouveau système d'API boursière
Alpha Vantage -> EODHD -> Finnhub
"""

import sys
import os
import time
import logging
import requests
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_new_api_manager():
    """Test du nouveau gestionnaire d'API"""
    try:
        logger.info("🧪 Test du nouveau gestionnaire d'API")
        
        from stock_api_manager import stock_api_manager
        
        symbols = ["AAPL", "TSLA", "MSFT", "IREN.SW"]
        
        for symbol in symbols:
            try:
                logger.info(f"📞 Test {symbol}")
                result = stock_api_manager.get_stock_price(symbol)
                
                if result and result.get('price', 0) > 0:
                    logger.info(f"   ✅ Prix: {result['price']} {result.get('currency', 'USD')}")
                    logger.info(f"   📊 Source: {result.get('source', 'N/A')}")
                    logger.info(f"   📈 Change: {result.get('change_percent', 'N/A')}%")
                else:
                    logger.error(f"   ❌ Pas de données pour {symbol}")
                    
            except Exception as e:
                logger.error(f"   ❌ Erreur pour {symbol}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test gestionnaire: {e}")
        return False

def test_individual_apis():
    """Test des APIs individuelles"""
    try:
        logger.info("🧪 Test des APIs individuelles")
        
        from stock_api_manager import AlphaVantageAPI, EODHDAPI, FinnhubAPI
        
        symbol = "AAPL"
        
        # Test Alpha Vantage
        try:
            logger.info(f"📞 Test Alpha Vantage pour {symbol}")
            alpha_vantage = AlphaVantageAPI()
            result = alpha_vantage.get_stock_price(symbol)
            
            if result and result.get('price', 0) > 0:
                logger.info(f"   ✅ Alpha Vantage: {result['price']} USD")
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
            else:
                logger.warning(f"   ⚠️ Finnhub: pas de données")
        except Exception as e:
            logger.error(f"   ❌ Finnhub: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test APIs individuelles: {e}")
        return False

def test_environment_variables():
    """Test des variables d'environnement"""
    try:
        logger.info("🧪 Test des variables d'environnement")
        
        # Variables importantes
        important_vars = [
            'ALPHA_VANTAGE_KEY',
            'EODHD_KEY',
            'FINNHUB_KEY'
        ]
        
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                # Masquer partiellement la valeur
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
                logger.info(f"✅ {var}: {masked}")
            else:
                logger.warning(f"⚠️ {var}: Non définie")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test variables: {e}")
        return False

def test_app_integration():
    """Test de l'intégration dans app.py"""
    try:
        logger.info("🧪 Test intégration app.py")
        
        # Vérifier si app.py utilise le nouveau gestionnaire
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifications
        checks = {
            'stock_api_manager': 'stock_api_manager' in content,
            'get_stock_price_stable': 'get_stock_price_stable' in content,
            'get_stock_price_manus': 'get_stock_price_manus' in content
        }
        
        logger.info("📋 Intégration dans app.py:")
        for module, integrated in checks.items():
            status = "✅" if integrated else "❌"
            logger.info(f"   {status} {module}")
        
        # Vérifier la route API
        if 'get_stock_price_stable(symbol)' in content:
            logger.info("✅ Route API utilise le nouveau gestionnaire")
        else:
            logger.error("❌ Route API n'utilise pas le nouveau gestionnaire")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test intégration: {e}")
        return False

def test_production_deployment():
    """Test de l'app en production"""
    try:
        logger.info("🧪 Test production")
        
        # URL de production
        production_url = "https://inventorysbo.onrender.com"
        
        # Test de base
        try:
            response = requests.get(f"{production_url}/", timeout=10)
            logger.info(f"✅ App accessible: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ App non accessible: {e}")
            return False
        
        # Test API stock price
        symbol = "AAPL"
        try:
            logger.info(f"📞 Test API {symbol}")
            response = requests.get(f"{production_url}/api/stock-price/{symbol}", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stock_data = data.get('data', {})
                    price = stock_data.get('price', 0)
                    source = stock_data.get('source', 'N/A')
                    
                    logger.info(f"   Prix: {price}")
                    logger.info(f"   Source: {source}")
                    
                    if price > 0:
                        logger.info(f"   ✅ Prix correct: {price}")
                        return True
                    else:
                        logger.error(f"   ❌ Prix invalide: {price}")
                        return False
                else:
                    logger.error(f"   ❌ API error: {data.get('error')}")
                    return False
            else:
                logger.error(f"   ❌ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"   ❌ Erreur API: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur test production: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Test du nouveau système d'API")
    
    # Test 1: Variables d'environnement
    logger.info("\n" + "="*50)
    test_environment_variables()
    
    # Test 2: APIs individuelles
    logger.info("\n" + "="*50)
    test_individual_apis()
    
    # Test 3: Gestionnaire complet
    logger.info("\n" + "="*50)
    test_new_api_manager()
    
    # Test 4: Intégration app.py
    logger.info("\n" + "="*50)
    test_app_integration()
    
    # Test 5: Production
    logger.info("\n" + "="*50)
    test_production_deployment()
    
    # Résumé
    logger.info("\n" + "="*50)
    logger.info("📋 TESTS TERMINÉS")
    logger.info("🔍 Vérifiez les logs ci-dessus pour identifier les problèmes")

if __name__ == "__main__":
    main() 