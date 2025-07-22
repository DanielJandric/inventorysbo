#!/usr/bin/env python3
"""
Fallback Alpha Vantage pour remplacer yfinance sur Render
"""

import os
import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def rate_limit(calls_per_minute=5):
    """Décorateur pour limiter les appels API à 5 par minute"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                logger.info(f"⏳ Rate limiting: attente {left_to_wait:.2f}s (max 5 req/min)")
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

class AlphaVantageFallback:
    """Fallback vers Alpha Vantage API"""
    
    def __init__(self):
        self.api_key = os.environ.get('ALPHA_VANTAGE_KEY')
        if not self.api_key:
            logger.warning("⚠️ ALPHA_VANTAGE_KEY non définie dans l'environnement")
        self.base_url = 'https://www.alphavantage.co/query'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    @rate_limit(calls_per_minute=5)
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère le prix d'une action via Alpha Vantage (rate limité à 5 req/min)"""
        try:
            logger.info(f"🔄 Tentative Alpha Vantage pour {symbol}")
            
            # Paramètres de la requête
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            # Faire la requête
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier si on a des données
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    
                    # Extraire les données
                    price_data = {
                        'symbol': symbol,
                        'name': symbol,  # Alpha Vantage ne donne pas le nom complet
                        'price': float(quote.get('05. price', 0)),
                        'change': float(quote.get('09. change', 0)),
                        'change_percent': float(quote.get('10. change percent', '0%').replace('%', '')),
                        'volume': int(quote.get('06. volume', 0)),
                        'market_cap': None,  # Alpha Vantage ne donne pas cette info
                        'pe_ratio': None,
                        'high_52_week': None,
                        'low_52_week': None,
                        'open': float(quote.get('02. open', 0)),
                        'previous_close': float(quote.get('08. previous close', 0)),
                        'currency': self._get_currency_for_symbol(symbol),
                        'exchange': 'NASDAQ',  # Par défaut
                        'last_updated': datetime.now().isoformat(),
                        'source': 'Alpha Vantage API',
                        'status': 'fallback_success',
                        'fallback_reason': 'yfinance blocked on Render'
                    }
                    
                    if price_data['price'] > 0:
                        logger.info(f"✅ Alpha Vantage réussi pour {symbol}: {price_data['price']} {price_data['currency']}")
                        return price_data
                    else:
                        logger.warning(f"⚠️ Alpha Vantage: prix invalide pour {symbol}")
                        return None
                else:
                    logger.warning(f"⚠️ Alpha Vantage: pas de données pour {symbol}")
                    return None
            else:
                logger.error(f"❌ Alpha Vantage erreur HTTP {response.status_code} pour {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur Alpha Vantage pour {symbol}: {e}")
            return None
    
    def _get_currency_for_symbol(self, symbol: str) -> str:
        """Détermine la devise pour un symbole"""
        # Mapping des devises (même logique que manus_integration)
        currency_map = {
            # Actions américaines
            "AAPL": "USD", "TSLA": "USD", "MSFT": "USD", "GOOGL": "USD",
            
            # Actions suisses (.SW)
            "IREN.SW": "CHF", "NOVN.SW": "CHF", "ROG.SW": "CHF",
            
            # Actions européennes
            "ASML": "EUR", "SAP": "EUR",
            
            # Actions britanniques
            "HSBA": "GBP", "BP": "GBP"
        }
        
        return currency_map.get(symbol, "USD")

# Instance globale
alpha_vantage_fallback = AlphaVantageFallback() 