#!/usr/bin/env python3
"""
Debug du problème des prix à 1.0
Diagnostic complet de l'API en production
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

def test_production_api():
    """Test de l'API en production"""
    try:
        # URL de votre app Render (à adapter)
        production_url = "https://inventorysbo.onrender.com"
        
        logger.info("🧪 Test de l'API en production")
        logger.info(f"📡 URL: {production_url}")
        
        # Test 1: Endpoint de base
        try:
            response = requests.get(f"{production_url}/", timeout=10)
            logger.info(f"✅ App accessible: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ App non accessible: {e}")
            return False
        
        # Test 2: API stock price
        symbols = ["AAPL", "TSLA", "MSFT"]
        
        for symbol in symbols:
            try:
                logger.info(f"📞 Test prix pour {symbol}")
                response = requests.get(f"{production_url}/api/stock-price/{symbol}", timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    price = data.get('price', 0)
                    source = data.get('source', 'N/A')
                    status = data.get('status', 'N/A')
                    
                    logger.info(f"   Prix: {price}")
                    logger.info(f"   Source: {source}")
                    logger.info(f"   Status: {status}")
                    
                    if price == 1.0:
                        logger.error(f"   ❌ PROBLÈME: Prix à 1.0 pour {symbol}")
                    elif price > 0:
                        logger.info(f"   ✅ Prix correct pour {symbol}")
                    else:
                        logger.warning(f"   ⚠️ Prix invalide pour {symbol}")
                        
                else:
                    logger.error(f"   ❌ Erreur HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"   ❌ Erreur pour {symbol}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test production: {e}")
        return False

def test_local_modules():
    """Test des modules locaux"""
    try:
        logger.info("🧪 Test des modules locaux")
        
        # Test 1: manus_integration
        try:
            from manus_integration import ManusStockAPI
            manus = ManusStockAPI()
            result = manus.get_stock_price("AAPL")
            
            logger.info(f"📊 Manus local - Prix: {result.get('price')}")
            logger.info(f"📊 Manus local - Source: {result.get('source')}")
            logger.info(f"📊 Manus local - Status: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"❌ Erreur manus_integration: {e}")
        
        # Test 2: alpha_vantage_fallback
        try:
            from alpha_vantage_fallback import alpha_vantage_fallback
            result = alpha_vantage_fallback.get_stock_price("AAPL")
            
            if result:
                logger.info(f"📊 Alpha Vantage local - Prix: {result.get('price')}")
                logger.info(f"📊 Alpha Vantage local - Source: {result.get('source')}")
            else:
                logger.warning("⚠️ Alpha Vantage local - Pas de données")
                
        except Exception as e:
            logger.error(f"❌ Erreur alpha_vantage_fallback: {e}")
        
        # Test 3: stable_manus_wrapper
        try:
            from stable_manus_wrapper import stable_manus_api
            result = stable_manus_api.get_stock_price("AAPL")
            
            logger.info(f"📊 Stable wrapper local - Prix: {result.get('price')}")
            logger.info(f"📊 Stable wrapper local - Source: {result.get('source')}")
            
        except Exception as e:
            logger.error(f"❌ Erreur stable_manus_wrapper: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test modules locaux: {e}")
        return False

def test_app_integration():
    """Test de l'intégration dans app.py"""
    try:
        logger.info("🧪 Test intégration app.py")
        
        # Vérifier si app.py utilise les nouveaux modules
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifications
        checks = {
            'manus_integration': 'manus_integration' in content,
            'alpha_vantage_fallback': 'alpha_vantage_fallback' in content,
            'stable_manus_wrapper': 'stable_manus_wrapper' in content,
            'get_stock_price_manus': 'get_stock_price_manus' in content
        }
        
        logger.info("📋 Intégration dans app.py:")
        for module, integrated in checks.items():
            status = "✅" if integrated else "❌"
            logger.info(f"   {status} {module}")
        
        # Vérifier la route API
        if '/api/stock-price/' in content:
            logger.info("✅ Route API trouvée")
        else:
            logger.error("❌ Route API manquante")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test intégration: {e}")
        return False

def test_environment_variables():
    """Test des variables d'environnement"""
    try:
        logger.info("🧪 Test variables d'environnement")
        
        # Variables importantes
        important_vars = [
            'ALPHA_VANTAGE_KEY',
            'SUPABASE_URL',
            'SUPABASE_KEY'
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

def test_alpha_vantage_key():
    """Test spécifique de la clé Alpha Vantage"""
    try:
        logger.info("🧪 Test clé Alpha Vantage")
        
        from alpha_vantage_fallback import alpha_vantage_fallback
        
        # Test direct
        result = alpha_vantage_fallback.get_stock_price("AAPL")
        
        if result and result.get('price', 0) > 0:
            logger.info(f"✅ Clé Alpha Vantage fonctionne: {result['price']} USD")
            return True
        else:
            logger.error("❌ Clé Alpha Vantage ne fonctionne pas")
            
            # Vérifier la clé
            key = alpha_vantage_fallback.api_key
            if key == 'demo':
                logger.error("❌ Utilise la clé 'demo' au lieu de la vraie clé")
            elif key:
                logger.info("✅ Clé correcte configurée")
            else:
                logger.warning("⚠️ Clé non définie")
            
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur test clé Alpha Vantage: {e}")
        return False

def main():
    """Fonction principale de debug"""
    logger.info("🚀 Début du diagnostic des prix à 1.0")
    
    # Test 1: Variables d'environnement
    logger.info("\n" + "="*50)
    test_environment_variables()
    
    # Test 2: Modules locaux
    logger.info("\n" + "="*50)
    test_local_modules()
    
    # Test 3: Intégration app.py
    logger.info("\n" + "="*50)
    test_app_integration()
    
    # Test 4: Clé Alpha Vantage
    logger.info("\n" + "="*50)
    test_alpha_vantage_key()
    
    # Test 5: API production (si accessible)
    logger.info("\n" + "="*50)
    test_production_api()
    
    # Résumé
    logger.info("\n" + "="*50)
    logger.info("📋 DIAGNOSTIC TERMINÉ")
    logger.info("🔍 Vérifiez les logs ci-dessus pour identifier le problème")

if __name__ == "__main__":
    main() 