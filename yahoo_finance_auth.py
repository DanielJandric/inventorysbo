#!/usr/bin/env python3
"""
Module d'authentification Yahoo Finance robuste
Utilise yfinance avec gestion d'erreurs améliorée pour éviter les erreurs 429 et "Invalid Crumb"
"""

import yfinance as yf
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class YahooFinanceAuth:
    """Gestionnaire d'authentification Yahoo Finance avec yfinance et gestion d'erreurs robuste"""
    
    def __init__(self):
        self.last_request_time = None
        self.min_request_interval = 1.0  # Délai minimum entre les requêtes (secondes)
        self.max_retries = 3
        self.retry_delay = 2  # secondes de base
        self.session_errors = 0
        self.max_session_errors = 5
        
        # Configuration yfinance
        self.yf_config = {
            'timeout': 10,
            'retries': 2,
            'backoff_factor': 0.5
        }
        
        logger.info("✅ Module d'authentification Yahoo Finance initialisé avec yfinance")
    
    def _wait_between_requests(self):
        """Attend entre les requêtes pour éviter les rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed + random.uniform(0.1, 0.5)
                time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _handle_yfinance_error(self, error: Exception, symbol: str, retry_count: int) -> bool:
        """Gère les erreurs yfinance avec stratégies de récupération"""
        error_str = str(error).lower()
        
        # Erreurs d'authentification
        if any(keyword in error_str for keyword in ['invalid crumb', 'unauthorized', '401']):
            logger.warning(f"⚠️ Erreur d'authentification pour {symbol}, tentative de récupération...")
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay * (retry_count + 1))
                return True  # Réessayer
        
        # Rate limiting
        elif any(keyword in error_str for keyword in ['429', 'too many requests', 'rate limit']):
            logger.warning(f"⚠️ Rate limit pour {symbol}, attente...")
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay * (2 ** retry_count))  # Backoff exponentiel
                return True  # Réessayer
        
        # Erreurs de réseau
        elif any(keyword in error_str for keyword in ['timeout', 'connection', 'network']):
            logger.warning(f"⚠️ Erreur réseau pour {symbol}, tentative de récupération...")
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return True  # Réessayer
        
        # Erreurs de données
        elif any(keyword in error_str for keyword in ['no data', 'empty', 'not found']):
            logger.warning(f"⚠️ Aucune donnée pour {symbol}")
            return False  # Ne pas réessayer
        
        # Autres erreurs
        else:
            logger.error(f"❌ Erreur inconnue pour {symbol}: {error}")
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return True  # Réessayer
        
        return False  # Ne pas réessayer
    
    def get_stock_data(self, symbol: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une action avec gestion automatique des erreurs"""
        try:
            self._wait_between_requests()
            
            logger.info(f"📊 Récupération données pour {symbol} (tentative {retry_count + 1})")
            
            # Créer un ticker yfinance
            ticker = yf.Ticker(symbol)
            
            # Récupérer les données historiques
            hist = ticker.history(period="1d", timeout=self.yf_config['timeout'])
            
            if hist.empty:
                logger.warning(f"⚠️ Aucune donnée historique pour {symbol}")
                return None
            
            # Récupérer les informations du ticker
            try:
                info = ticker.info
            except Exception as info_error:
                logger.warning(f"⚠️ Impossible de récupérer les infos pour {symbol}: {info_error}")
                info = {}
            
            # Extraire les données
            current_price = float(hist['Close'].iloc[-1])
            open_price = float(hist['Open'].iloc[0])
            volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
            high = float(hist['High'].iloc[-1]) if 'High' in hist.columns else current_price
            low = float(hist['Low'].iloc[-1]) if 'Low' in hist.columns else current_price
            
            # Calculer les variations
            change = current_price - open_price
            change_percent = (change / open_price) * 100 if open_price > 0 else 0
            
            return {
                'symbol': symbol,
                'price': current_price,
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', ''),
                'timestamp': datetime.now().isoformat(),
                'volume': volume,
                'high': high,
                'low': low,
                'open': open_price,
                'change': change,
                'change_percent': change_percent,
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
                'high_52_week': info.get('fiftyTwoWeekHigh'),
                'low_52_week': info.get('fiftyTwoWeekLow')
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données pour {symbol}: {e}")
            
            # Gérer les erreurs avec stratégie de récupération
            if self._handle_yfinance_error(e, symbol, retry_count) and retry_count < self.max_retries:
                return self.get_stock_data(symbol, retry_count + 1)
            
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations détaillées d'une action"""
        try:
            self._wait_between_requests()
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if info:
                return info
            else:
                logger.warning(f"⚠️ Aucune information détaillée pour {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des infos pour {symbol}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Teste la connexion et l'authentification"""
        try:
            logger.info("🧪 Test de connexion Yahoo Finance...")
            
            test_data = self.get_stock_data("AAPL")
            if test_data:
                logger.info("✅ Test de connexion Yahoo Finance réussi")
                return True
            else:
                logger.error("❌ Test de connexion Yahoo Finance échoué")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de connexion: {e}")
            return False
    
    def get_multiple_stocks(self, symbols: list) -> Dict[str, Optional[Dict[str, Any]]]:
        """Récupère les données de plusieurs actions avec gestion d'erreurs"""
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol)
                results[symbol] = data
                
                # Pause entre les symboles pour éviter les rate limits
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                logger.error(f"❌ Erreur pour {symbol}: {e}")
                results[symbol] = None
        
        return results

# Fonction utilitaire pour obtenir une instance
def get_yahoo_auth() -> YahooFinanceAuth:
    """Retourne une instance d'authentification Yahoo Finance"""
    return YahooFinanceAuth()

if __name__ == "__main__":
    # Test du module
    logging.basicConfig(level=logging.INFO)
    
    auth = YahooFinanceAuth()
    
    # Test de connexion
    if auth.test_connection():
        print("✅ Module d'authentification Yahoo Finance opérationnel")
        
        # Test avec quelques symboles
        symbols = ["AAPL", "MSFT", "GOOGL"]
        for symbol in symbols:
            data = auth.get_stock_data(symbol)
            if data:
                print(f"✅ {symbol}: ${data['price']:.2f} {data['currency']} ({data['change_percent']:+.2f}%)")
            else:
                print(f"❌ {symbol}: Erreur")
    else:
        print("❌ Module d'authentification Yahoo Finance non opérationnel") 