#!/usr/bin/env python3
"""
Module de fallback Yahoo Finance avec yahooquery
Utilisé quand l'API directe Yahoo Finance échoue
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

try:
    from yahooquery import Ticker
    YAHOOQUERY_AVAILABLE = True
except ImportError:
    YAHOOQUERY_AVAILABLE = False
    logger.warning("⚠️ yahooquery non disponible")

class YahooQueryFallback:
    """Fallback utilisant yahooquery pour les données Yahoo Finance"""
    
    def __init__(self):
        self.cache = {}
        self.last_request_time = None
        self.min_request_interval = 0.5  # Délai minimum entre les requêtes
        
        if not YAHOOQUERY_AVAILABLE:
            raise ImportError("yahooquery n'est pas installé")
        
        logger.info("✅ Module de fallback yahooquery initialisé")
    
    def _wait_between_requests(self):
        """Attend entre les requêtes pour éviter les rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une action via yahooquery"""
        try:
            self._wait_between_requests()
            
            logger.info(f"📊 Récupération données via yahooquery pour {symbol}")
            
            # Créer un ticker yahooquery
            ticker = Ticker(symbol)
            
            # Récupérer les prix
            price_data = ticker.price
            
            # Vérifier que price_data est un dictionnaire
            if not isinstance(price_data, dict):
                logger.error(f"❌ yahooquery retourne un type invalide pour {symbol}: {type(price_data)}")
                return None
            
            if symbol in price_data and price_data[symbol]:
                price_info = price_data[symbol]
                
                # Extraire les données essentielles
                current_price = price_info.get('regularMarketPrice')
                if current_price:
                    return {
                        'symbol': symbol,
                        'price': current_price,
                        'currency': price_info.get('currency', 'USD'),
                        'exchange': price_info.get('fullExchangeName', ''),
                        'timestamp': datetime.now().isoformat(),
                        'volume': price_info.get('regularMarketVolume'),
                        'high': price_info.get('regularMarketDayHigh'),
                        'low': price_info.get('regularMarketDayLow'),
                        'open': price_info.get('regularMarketOpen'),
                        'change': price_info.get('regularMarketChange'),
                        'change_percent': price_info.get('regularMarketChangePercent'),
                        'market_cap': price_info.get('marketCap'),
                        'pe_ratio': price_info.get('trailingPE'),
                        'dividend_yield': price_info.get('trailingAnnualDividendYield'),
                        'high_52_week': price_info.get('fiftyTwoWeekHigh'),
                        'low_52_week': price_info.get('fiftyTwoWeekLow'),
                        'previous_close': price_info.get('regularMarketPreviousClose')
                    }
            
            logger.warning(f"⚠️ Aucune donnée yahooquery pour {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur yahooquery pour {symbol}: {e}")
            return None
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Récupère les données de plusieurs actions"""
        results = {}
        
        try:
            self._wait_between_requests()
            
            logger.info(f"📊 Récupération données multiples via yahooquery pour {len(symbols)} symboles")
            
            # Créer un ticker pour tous les symboles
            ticker = Ticker(symbols)
            
            # Récupérer les prix
            price_data = ticker.price
            
            # Vérifier que price_data est un dictionnaire
            if not isinstance(price_data, dict):
                logger.error(f"❌ yahooquery retourne un type invalide pour les symboles multiples: {type(price_data)}")
                for symbol in symbols:
                    results[symbol] = None
                return results
            
            for symbol in symbols:
                if symbol in price_data and price_data[symbol]:
                    price_info = price_data[symbol]
                    
                    current_price = price_info.get('regularMarketPrice')
                    if current_price:
                        results[symbol] = {
                            'symbol': symbol,
                            'price': current_price,
                            'currency': price_info.get('currency', 'USD'),
                            'exchange': price_info.get('fullExchangeName', ''),
                            'timestamp': datetime.now().isoformat(),
                            'volume': price_info.get('regularMarketVolume'),
                            'high': price_info.get('regularMarketDayHigh'),
                            'low': price_info.get('regularMarketDayLow'),
                            'open': price_info.get('regularMarketOpen'),
                            'change': price_info.get('regularMarketChange'),
                            'change_percent': price_info.get('regularMarketChangePercent'),
                            'market_cap': price_info.get('marketCap'),
                            'pe_ratio': price_info.get('trailingPE'),
                            'dividend_yield': price_info.get('trailingAnnualDividendYield'),
                            'high_52_week': price_info.get('fiftyTwoWeekHigh'),
                            'low_52_week': price_info.get('fiftyTwoWeekLow'),
                            'previous_close': price_info.get('regularMarketPreviousClose')
                        }
                    else:
                        results[symbol] = None
                else:
                    results[symbol] = None
            
        except Exception as e:
            logger.error(f"❌ Erreur yahooquery multiple: {e}")
            for symbol in symbols:
                results[symbol] = None
        
        return results
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations détaillées d'une action"""
        try:
            self._wait_between_requests()
            
            ticker = Ticker(symbol)
            
            # Récupérer les informations détaillées
            info = ticker.asset_profile
            
            if symbol in info and info[symbol]:
                return info[symbol]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur yahooquery info pour {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[Dict[str, Any]]:
        """Récupère les données historiques d'une action"""
        try:
            self._wait_between_requests()
            
            ticker = Ticker(symbol)
            hist = ticker.history(period=period)
            
            if not hist.empty:
                return {
                    'data': hist.to_dict('records'),
                    'period': period,
                    'symbol': symbol
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur yahooquery historique pour {symbol}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Teste la connexion yahooquery"""
        try:
            logger.info("🧪 Test de connexion yahooquery...")
            
            test_data = self.get_stock_data("AAPL")
            if test_data:
                logger.info("✅ Test de connexion yahooquery réussi")
                return True
            else:
                logger.error("❌ Test de connexion yahooquery échoué")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de connexion yahooquery: {e}")
            return False

# Fonction utilitaire pour obtenir une instance
def get_yahoo_fallback() -> YahooQueryFallback:
    """Retourne une instance de fallback yahooquery"""
    return YahooQueryFallback()

if __name__ == "__main__":
    # Test du module
    logging.basicConfig(level=logging.INFO)
    
    try:
        fallback = YahooQueryFallback()
        
        # Test de connexion
        if fallback.test_connection():
            print("✅ Module de fallback yahooquery opérationnel")
            
            # Test avec quelques symboles
            symbols = ["AAPL", "MSFT", "GOOGL"]
            for symbol in symbols:
                data = fallback.get_stock_data(symbol)
                if data:
                    print(f"✅ {symbol}: ${data['price']:.2f} {data['currency']} ({data['change_percent']:+.2f}%)")
                else:
                    print(f"❌ {symbol}: Erreur")
        else:
            print("❌ Module de fallback yahooquery non opérationnel")
            
    except ImportError as e:
        print(f"❌ yahooquery non disponible: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}") 