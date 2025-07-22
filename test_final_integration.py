#!/usr/bin/env python3
"""
Test final de l'intégration complète
Vérifie que le wrapper stable fonctionne dans app.py
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

def test_stable_wrapper_direct():
    """Test direct du wrapper stable"""
    try:
        logger.info("🧪 Test direct du wrapper stable")
        
        from stable_manus_wrapper import get_stock_price_stable
        
        symbols = ["AAPL", "TSLA", "MSFT"]
        
        for symbol in symbols:
            try:
                logger.info(f"📞 Test {symbol}")
                result = get_stock_price_stable(symbol)
                
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
        logger.error(f"❌ Erreur test wrapper direct: {e}")
        return False

def test_app_integration():
    """Test de l'intégration dans app.py"""
    try:
        logger.info("🧪 Test intégration app.py")
        
        # Vérifier les imports
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifications
        checks = {
            'alpha_vantage_fallback': 'alpha_vantage_fallback' in content,
            'stable_manus_wrapper': 'stable_manus_wrapper' in content,
            'get_stock_price_stable': 'get_stock_price_stable' in content,
            'stable_manus_api': 'stable_manus_api' in content
        }
        
        logger.info("📋 Intégration dans app.py:")
        for module, integrated in checks.items():
            status = "✅" if integrated else "❌"
            logger.info(f"   {status} {module}")
        
        # Vérifier la route API
        if 'get_stock_price_stable(symbol)' in content:
            logger.info("✅ Route API utilise le wrapper stable")
        else:
            logger.error("❌ Route API n'utilise pas le wrapper stable")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test intégration: {e}")
        return False

def test_local_app():
    """Test de l'app locale (si possible)"""
    try:
        logger.info("🧪 Test app locale")
        
        # Importer app.py
        import app
        
        # Test de la fonction get_stock_price_stable
        from stable_manus_wrapper import get_stock_price_stable
        
        symbol = "AAPL"
        result = get_stock_price_stable(symbol)
        
        if result and result.get('price', 0) > 0:
            logger.info(f"✅ App locale fonctionne: {result['price']} {result.get('currency', 'USD')}")
            return True
        else:
            logger.error("❌ App locale ne retourne pas de données")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur test app locale: {e}")
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

def test_alpha_vantage_key():
    """Test de la clé Alpha Vantage"""
    try:
        logger.info("🧪 Test clé Alpha Vantage")
        
        # Vérifier la variable d'environnement
        key = os.environ.get('ALPHA_VANTAGE_KEY')
        if not key:
            logger.warning("⚠️ ALPHA_VANTAGE_KEY non définie")
            # Utiliser la clé par défaut
            key = 'XCRQGI1OMS5381DE'
            logger.info(f"   Utilisation clé par défaut: {key[:4]}...")
        
        # Test direct Alpha Vantage
        from alpha_vantage_fallback import alpha_vantage_fallback
        
        result = alpha_vantage_fallback.get_stock_price("AAPL")
        
        if result and result.get('price', 0) > 0:
            logger.info(f"✅ Alpha Vantage fonctionne: {result['price']} USD")
            return True
        else:
            logger.error("❌ Alpha Vantage ne fonctionne pas")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur test Alpha Vantage: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Test final de l'intégration complète")
    
    # Test 1: Wrapper stable direct
    logger.info("\n" + "="*50)
    test_stable_wrapper_direct()
    
    # Test 2: Intégration app.py
    logger.info("\n" + "="*50)
    test_app_integration()
    
    # Test 3: Clé Alpha Vantage
    logger.info("\n" + "="*50)
    test_alpha_vantage_key()
    
    # Test 4: App locale
    logger.info("\n" + "="*50)
    test_local_app()
    
    # Test 5: Production
    logger.info("\n" + "="*50)
    test_production_deployment()
    
    # Résumé
    logger.info("\n" + "="*50)
    logger.info("📋 TESTS TERMINÉS")
    logger.info("🔍 Vérifiez les logs ci-dessus pour identifier les problèmes")

if __name__ == "__main__":
    main() 