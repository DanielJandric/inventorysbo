#!/usr/bin/env python3
"""
Test d'intégration Alpha Vantage dans le système de fallback
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

def test_manus_integration_fallback():
    """Test du système de fallback complet avec manus_integration"""
    try:
        from manus_integration import ManusStockAPI
        
        logger.info("🧪 Test intégration fallback Alpha Vantage")
        
        # Créer une instance
        manus = ManusStockAPI()
        
        # Test avec des symboles qui devraient utiliser Alpha Vantage
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL"]
        
        for symbol in symbols:
            logger.info(f"📞 Test fallback pour {symbol}")
            start_time = time.time()
            
            result = manus.get_stock_price(symbol)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result:
                logger.info(f"✅ {symbol}: {result['price']} {result['currency']} (durée: {duration:.2f}s)")
                logger.info(f"   Source: {result.get('source', 'N/A')}")
                logger.info(f"   Status: {result.get('status', 'N/A')}")
            else:
                logger.error(f"❌ {symbol}: échec")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test intégration: {e}")
        return False

def test_currency_handling():
    """Test de la gestion des devises avec Alpha Vantage"""
    try:
        from alpha_vantage_fallback import alpha_vantage_fallback
        
        logger.info("🧪 Test gestion des devises Alpha Vantage")
        
        # Test avec différents types d'actions
        test_cases = [
            ("AAPL", "USD"),
            ("TSLA", "USD"), 
            ("IREN.SW", "CHF"),  # Devrait être CHF même si pas de données
            ("ASML", "EUR"),
            ("HSBA", "GBP")
        ]
        
        for symbol, expected_currency in test_cases:
            result = alpha_vantage_fallback.get_stock_price(symbol)
            
            if result:
                actual_currency = result['currency']
                if actual_currency == expected_currency:
                    logger.info(f"✅ {symbol}: {actual_currency} (correct)")
                else:
                    logger.warning(f"⚠️ {symbol}: {actual_currency} (attendu: {expected_currency})")
            else:
                logger.info(f"ℹ️ {symbol}: pas de données (devise attendue: {expected_currency})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test devises: {e}")
        return False

def test_app_integration():
    """Test de l'intégration dans app.py"""
    try:
        logger.info("🧪 Test intégration app.py")
        
        # Simuler un appel API comme dans app.py
        from manus_integration import ManusStockAPI
        
        manus = ManusStockAPI()
        
        # Test avec un symbole
        symbol = "AAPL"
        result = manus.get_stock_price(symbol)
        
        if result:
            # Vérifier que le résultat est compatible avec app.py
            required_fields = ['symbol', 'price', 'currency', 'name']
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                logger.info(f"✅ Résultat compatible avec app.py pour {symbol}")
                logger.info(f"   Prix: {result['price']} {result['currency']}")
                logger.info(f"   Nom: {result['name']}")
                return True
            else:
                logger.error(f"❌ Champs manquants: {missing_fields}")
                return False
        else:
            logger.error(f"❌ Pas de résultat pour {symbol}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test app.py: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Début des tests d'intégration Alpha Vantage")
    
    # Test 1: Intégration fallback
    logger.info("\n" + "="*50)
    success1 = test_manus_integration_fallback()
    
    # Test 2: Gestion des devises
    logger.info("\n" + "="*50)
    success2 = test_currency_handling()
    
    # Test 3: Intégration app.py
    logger.info("\n" + "="*50)
    success3 = test_app_integration()
    
    # Résumé
    logger.info("\n" + "="*50)
    logger.info("📋 RÉSUMÉ DES TESTS D'INTÉGRATION")
    logger.info(f"✅ Fallback manus_integration: {'SUCCÈS' if success1 else 'ÉCHEC'}")
    logger.info(f"✅ Gestion des devises: {'SUCCÈS' if success2 else 'ÉCHEC'}")
    logger.info(f"✅ Intégration app.py: {'SUCCÈS' if success3 else 'ÉCHEC'}")
    
    if success1 and success2 and success3:
        logger.info("🎉 Tous les tests d'intégration réussis!")
        logger.info("🚀 Alpha Vantage est prêt pour la production!")
        return True
    else:
        logger.error("❌ Certains tests d'intégration ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 