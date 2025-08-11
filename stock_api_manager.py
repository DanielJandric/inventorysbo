#!/usr/bin/env python3
"""
Gestionnaire d'API boursière avec fallback séquentiel
Alpha Vantage -> EODHD -> Finnhub
"""

import os
import time
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

def rate_limit(calls_per_minute=5):
    """Décorateur pour limiter les appels API"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                logger.info(f"⏳ Rate limiting: attente {left_to_wait:.2f}s (max {calls_per_minute} req/min)")
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

class AlphaVantageAPI:
    """API Alpha Vantage"""
    
    def __init__(self):
        self.api_key = os.environ.get('ALPHA_VANTAGE_KEY')
        if not self.api_key:
            logger.warning("⚠️ ALPHA_VANTAGE_KEY non définie dans l'environnement")
        self.base_url = 'https://www.alphavantage.co/query'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @rate_limit(calls_per_minute=5)
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère le prix d'une action via Alpha Vantage"""
        try:
            logger.info(f"🔄 Tentative Alpha Vantage pour {symbol}")
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                
                price = float(quote.get('05. price', 0))
                if price <= 0:
                    logger.warning(f"⚠️ Alpha Vantage: prix invalide pour {symbol}")
                    return None
                
                result = {
                    'price': price,
                    'currency': 'USD',  # Alpha Vantage retourne en USD
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': float(quote.get('10. change percent', '0').replace('%', '')),
                    'volume': int(quote.get('06. volume', 0)),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Alpha Vantage'
                }
                
                logger.info(f"✅ Alpha Vantage réussi pour {symbol}: {price} USD")
                return result
            else:
                logger.warning(f"⚠️ Alpha Vantage: pas de données pour {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur Alpha Vantage pour {symbol}: {e}")
            return None
    
    def _get_currency_for_symbol(self, symbol: str) -> str:
        """Mappe les symboles à leur devise"""
        currency_map = {
            'IREN.SW': 'CHF',
            'NOVN.SW': 'CHF',
            'ROG.SW': 'CHF',
            'NESN.SW': 'CHF',
            'UBSG.SW': 'CHF',
            'CSGN.SW': 'CHF',
            'ABBN.SW': 'CHF',
            'ZURN.SW': 'CHF',
            'LONN.SW': 'CHF',
            'GIVN.SW': 'CHF',
            'SIX.SW': 'CHF',
            'BAER.SW': 'CHF',
            'SREN.SW': 'CHF',
            'SCMN.SW': 'CHF',
            'SGSN.SW': 'CHF',
            'SLHN.SW': 'CHF',
            'TEMN.SW': 'CHF',
            'VIFN.SW': 'CHF',
            'ZUGN.SW': 'CHF',
            'AMS.SW': 'CHF',
            'ATLN.SW': 'CHF',
            'BALN.SW': 'CHF',
            'CLN.SW': 'CHF',
            'COPN.SW': 'CHF',
            'DKSH.SW': 'CHF',
            'EMMN.SW': 'CHF',
            'GEBN.SW': 'CHF',
            'GMI.SW': 'CHF',
            'HEID.SW': 'CHF',
            'HOLN.SW': 'CHF',
            'IMPN.SW': 'CHF',
            'KER.SW': 'CHF',
            'KNIN.SW': 'CHF',
            'LOGN.SW': 'CHF',
            'LONN.SW': 'CHF',
            'MOBN.SW': 'CHF',
            'MOVE.SW': 'CHF',
            'OREP.SW': 'CHF',
            'PSPN.SW': 'CHF',
            'RACE.SW': 'CHF',
            'RIGN.SW': 'CHF',
            'SCHP.SW': 'CHF',
            'SENS.SW': 'CHF',
            'SGSN.SW': 'CHF',
            'SHLTN.SW': 'CHF',
            'SIKA.SW': 'CHF',
            'SOON.SW': 'CHF',
            'STGN.SW': 'CHF',
            'SU.SW': 'CHF',
            'SWTQ.SW': 'CHF',
            'TECN.SW': 'CHF',
            'TEMN.SW': 'CHF',
            'UHR.SW': 'CHF',
            'VIFN.SW': 'CHF',
            'VONN.SW': 'CHF',
            'ZUGN.SW': 'CHF'
        }
        return currency_map.get(symbol, 'USD')

class EODHDAPI:
    """API EODHD"""
    
    def __init__(self):
        self.api_key = os.environ.get('EODHD_KEY')
        if not self.api_key:
            logger.warning("⚠️ EODHD_KEY non définie dans l'environnement")
        self.base_url = 'https://eodhd.com/api'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @rate_limit(calls_per_minute=10)
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère le prix d'une action via EODHD"""
        try:
            logger.info(f"🔄 Tentative EODHD pour {symbol}")
            
            url = f"{self.base_url}/real-time/{symbol}"
            params = {
                'api_token': self.api_key,
                'fmt': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and isinstance(data, dict):
                price = float(data.get('close', 0))
                if price <= 0:
                    logger.warning(f"⚠️ EODHD: prix invalide pour {symbol}")
                    return None
                
                result = {
                    'price': price,
                    'currency': data.get('currency', 'USD'),
                    'change': float(data.get('change', 0)),
                    'change_percent': float(data.get('change_p', 0)),
                    'volume': int(data.get('volume', 0)),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'EODHD'
                }
                
                logger.info(f"✅ EODHD réussi pour {symbol}: {price} {result['currency']}")
                return result
            else:
                logger.warning(f"⚠️ EODHD: pas de données pour {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur EODHD pour {symbol}: {e}")
            return None

class FinnhubAPI:
    """API Finnhub"""
    
    def __init__(self):
        self.api_key = os.environ.get('FINNHUB_KEY')
        if not self.api_key:
            logger.warning("⚠️ FINNHUB_KEY non définie dans l'environnement")
        self.base_url = 'https://finnhub.io/api/v1'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @rate_limit(calls_per_minute=60)
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère le prix d'une action via Finnhub"""
        try:
            logger.info(f"🔄 Tentative Finnhub pour {symbol}")
            
            url = f"{self.base_url}/quote"
            params = {
                'symbol': symbol,
                'token': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and isinstance(data, dict):
                price = float(data.get('c', 0))  # Current price
                if price <= 0:
                    logger.warning(f"⚠️ Finnhub: prix invalide pour {symbol}")
                    return None
                
                result = {
                    'price': price,
                    'currency': 'USD',  # Finnhub retourne en USD
                    'change': float(data.get('d', 0)),  # Change
                    'change_percent': float(data.get('dp', 0)),  # Change percent
                    'volume': int(data.get('v', 0)),  # Volume
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Finnhub'
                }
                
                logger.info(f"✅ Finnhub réussi pour {symbol}: {price} USD")
                return result
            else:
                logger.warning(f"⚠️ Finnhub: pas de données pour {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur Finnhub pour {symbol}: {e}")
            return None

class YFinanceAPI:
    """Yahoo Finance via yfinance (gratuit, robuste)"""

    def __init__(self):
        # yfinance est importé dynamiquement dans l'appel pour éviter les erreurs d'import au démarrage
        pass

    @rate_limit(calls_per_minute=90)
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère le prix d'une action via yfinance"""
        try:
            logger.info(f"🔄 Tentative yfinance pour {symbol}")
            try:
                import yfinance as yf  # type: ignore
            except Exception as e:
                logger.warning(f"⚠️ yfinance non disponible: {e}")
                return None

            ticker = yf.Ticker(symbol)
            price = None
            change = None
            change_percent = None
            volume = None
            currency = None
            fifty_two_week_high = None
            fifty_two_week_low = None
            pe_ratio = None

            # fast_info (plus fiable/rapide)
            fi = getattr(ticker, 'fast_info', None)
            if fi:
                getter = getattr(fi, 'get', None)
                if callable(getter):
                    price = getter('last_price') or getter('lastPrice') or getter('last')
                    prev_close = getter('previous_close') or getter('previousClose')
                    volume = getter('volume')
                    currency = getter('currency')
                    fifty_two_week_high = getter('yearHigh') or getter('fifty_two_week_high')
                    fifty_two_week_low = getter('yearLow') or getter('fifty_two_week_low')
                    if price and prev_close and prev_close != 0:
                        try:
                            change = float(price) - float(prev_close)
                            change_percent = (change / float(prev_close)) * 100.0
                        except Exception:
                            pass

            # Fallback sur info
            if price is None or currency is None or fifty_two_week_high is None or fifty_two_week_low is None or pe_ratio is None:
                try:
                    info = ticker.info or {}
                except Exception:
                    info = {}
                price = price if price is not None else info.get('currentPrice') or info.get('regularMarketPrice')
                currency = currency if currency is not None else info.get('currency')
                fifty_two_week_high = fifty_two_week_high if fifty_two_week_high is not None else (
                    info.get('fiftyTwoWeekHigh') or info.get('fifty_two_week_high')
                )
                fifty_two_week_low = fifty_two_week_low if fifty_two_week_low is not None else (
                    info.get('fiftyTwoWeekLow') or info.get('fifty_two_week_low')
                )
                pe_ratio = pe_ratio if pe_ratio is not None else (
                    info.get('trailingPE') or info.get('trailingPe') or info.get('forwardPE')
                )
                if change is None and info.get('regularMarketChange') is not None:
                    change = info.get('regularMarketChange')
                if change_percent is None and info.get('regularMarketChangePercent') is not None:
                    change_percent = float(info.get('regularMarketChangePercent')) * 100.0 if abs(info.get('regularMarketChangePercent')) < 1 else info.get('regularMarketChangePercent')
                if volume is None:
                    volume = info.get('regularMarketVolume')

            # Fallback ultime: l'historique du jour
            if price is None:
                try:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        price = float(hist['Close'].iloc[-1])
                        if currency is None:
                            currency = (ticker.get_info() or {}).get('currency')
                except Exception:
                    pass

            if price is None or (isinstance(price, (int, float)) and float(price) <= 0):
                logger.warning(f"⚠️ yfinance: prix invalide pour {symbol}")
                return None

            result = {
                'price': float(price),
                'currency': currency or 'USD',
                'change': float(change) if change is not None else None,
                'change_percent': float(change_percent) if change_percent is not None else None,
                'volume': int(volume) if volume is not None else None,
                'fifty_two_week_high': float(fifty_two_week_high) if fifty_two_week_high is not None else None,
                'fifty_two_week_low': float(fifty_two_week_low) if fifty_two_week_low is not None else None,
                'pe_ratio': float(pe_ratio) if pe_ratio is not None else None,
                'timestamp': datetime.now().isoformat(),
                'source': 'yfinance'
            }
            logger.info(f"✅ yfinance réussi pour {symbol}: {result['price']} {result['currency']}")
            return result
        except Exception as e:
            logger.error(f"❌ Erreur yfinance pour {symbol}: {e}")
            return None

class StockAPIManager:
    """Gestionnaire principal des APIs boursières"""
    
    def __init__(self):
        self.alpha_vantage = AlphaVantageAPI()
        self.eodhd = EODHDAPI()
        self.finnhub = FinnhubAPI()
        self.yfinance = YFinanceAPI()
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_stock_price(self, symbol: str, force_refresh=False) -> Optional[Dict[str, Any]]:
        """
        Récupère le prix d'une action en essayant les APIs en séquence
        Alpha Vantage -> EODHD -> Finnhub
        """
        # Vérifier le cache
        if not force_refresh and symbol in self.cache:
            cached_data = self.cache[symbol]
            if time.time() - cached_data['timestamp'] < self.cache_duration:
                logger.info(f"📋 Données en cache pour {symbol}")
                return cached_data['data']
        
        logger.info(f"🔍 Récupération prix pour {symbol}")
        
        # Essayer Alpha Vantage en premier
        result = self.alpha_vantage.get_stock_price(symbol)
        if result and result.get('price', 0) > 0:
            result = self._adjust_currency_for_swiss_stocks(symbol, result)
            self._cache_result(symbol, result)
            return result
        
        # Essayer EODHD
        result = self.eodhd.get_stock_price(symbol)
        if result and result.get('price', 0) > 0:
            result = self._adjust_currency_for_swiss_stocks(symbol, result)
            self._cache_result(symbol, result)
            return result
        
        # Essayer Finnhub
        result = self.finnhub.get_stock_price(symbol)
        if result and result.get('price', 0) > 0:
            result = self._adjust_currency_for_swiss_stocks(symbol, result)
            self._cache_result(symbol, result)
            return result

        # Essayer yfinance en dernier
        result = self.yfinance.get_stock_price(symbol)
        if result and result.get('price', 0) > 0:
            result = self._adjust_currency_for_swiss_stocks(symbol, result)
            self._cache_result(symbol, result)
            return result
        
        logger.error(f"❌ Toutes les APIs ont échoué pour {symbol}")
        return None
    
    def _cache_result(self, symbol: str, data: Dict[str, Any]):
        """Met en cache le résultat"""
        self.cache[symbol] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def clear_cache(self):
        """Vide le cache"""
        self.cache.clear()
        logger.info("🗑️ Cache vidé")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retourne le statut du cache"""
        return {
            'cache_size': len(self.cache),
            'cache_duration': self.cache_duration,
            'cached_symbols': list(self.cache.keys())
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retourne le statut de santé des APIs"""
        return {
            'alpha_vantage': {
                'key_configured': bool(self.alpha_vantage.api_key and self.alpha_vantage.api_key != 'demo'),
                'rate_limit': '5 req/min'
            },
            'eodhd': {
                'key_configured': bool(self.eodhd.api_key and self.eodhd.api_key != 'demo'),
                'rate_limit': '10 req/min'
            },
            'finnhub': {
                'key_configured': bool(self.finnhub.api_key and self.finnhub.api_key != 'demo'),
                'rate_limit': '60 req/min'
            },
            'cache': self.get_cache_status()
        }

    def _adjust_currency_for_swiss_stocks(self, symbol: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ajuste la devise pour les actions suisses (.SW)
        Force l'affichage en CHF pour les actions suisses
        """
        if symbol.endswith('.SW'):
            result['currency'] = 'CHF'
            logger.info(f"🇨🇭 Devise ajustée pour {symbol}: CHF")
        return result

    def get_market_snapshot(self) -> Dict[str, Any]:
        """Récupère un aperçu des principaux indicateurs de marché (version stricte yfinance).

        Exigences:
        - Utiliser yfinance uniquement
        - Attendre 11 secondes AVANT chaque requête
        - Inclure: NVDA, MSFT, AMD, AAPL, Or (Gold), Bitcoin, S&P 500, Nasdaq, Dow Jones, VIX
        - Ne pas inventer: si indisponible, retourner {"error": "Data not available"}
        """
        logger.info("📊 Récupération de l'aperçu du marché (mode strict yfinance)...")

        snapshot: Dict[str, Any] = {
            "stocks": {},
            "indices": {},
            "volatility": {},
            "commodities": {},
            "crypto": {},
            "forex": {},
            "bonds": {}
        }

        # Liste ordonnée des requêtes à effectuer (avec affichage)
        ordered_symbols = [
            ("stocks", "NVDA", "NVDA"),
            ("stocks", "MSFT", "MSFT"),
            ("stocks", "AMD", "AMD"),
            ("stocks", "AAPL", "AAPL"),
            ("commodities", "Or (Gold)", "GC=F"),
            ("crypto", "Bitcoin", "BTC-USD"),
            ("indices", "S&P 500", "^GSPC"),
            ("indices", "NASDAQ", "^IXIC"),
            ("indices", "Dow Jones", "^DJI"),
            ("indices", "Russell 2000", "^RUT"),
            ("volatility", "VIX", "^VIX"),
            ("commodities", "WTI", "CL=F"),
            ("commodities", "Brent", "BZ=F"),
            ("commodities", "Natural Gas", "NG=F"),
            ("crypto", "Ethereum", "ETH-USD"),
            ("forex", "DXY", "DX=F"),
            ("bonds", "US 10Y", "^TNX"),
        ]

        # Utiliser exclusivement yfinance
        for category, display_name, symbol in ordered_symbols:
            logger.info(f"⏳ Attente 10s avant la requête yfinance pour {symbol} ({display_name})...")
            time.sleep(10)
            data = self.yfinance.get_stock_price(symbol)
            if data and data.get('price') is not None:
                if category == 'bonds' and display_name == 'US 10Y':
                    # Yahoo ^TNX: 1 unit = 0.1% yield
                    yield_pct = float(data.get('price')) / 10.0
                    change_bps = float(data.get('change')) * 10.0 if data.get('change') is not None else None
                    snapshot[category][display_name] = {
                        "yield": round(yield_pct, 3),
                        "change_bps": round(change_bps, 1) if change_bps is not None else None,
                        "source": data.get('source')
                    }
                elif category == 'forex' and display_name == 'DXY':
                    snapshot[category][display_name] = {
                        "value": data.get('price'),
                        "change": data.get('change'),
                        "change_percent": data.get('change_percent'),
                        "source": data.get('source')
                    }
                else:
                    snapshot[category][display_name] = {
                        "price": data.get('price'),
                        "change": data.get('change'),
                        "change_percent": data.get('change_percent'),
                        "source": data.get('source')
                    }
            else:
                snapshot[category][display_name] = {"error": "Data not available"}

        logger.info("✅ Aperçu du marché (strict) récupéré.")
        return snapshot


# Instance globale
stock_api_manager = StockAPIManager()

# Fonctions de compatibilité
def get_stock_price_stable(symbol: str) -> Optional[Dict[str, Any]]:
    """Fonction de compatibilité avec l'ancien système"""
    return stock_api_manager.get_stock_price(symbol)

def get_stock_price_manus(symbol: str, item=None, cache_key=None, force_refresh=False) -> Optional[Dict[str, Any]]:
    """Fonction de compatibilité avec l'ancien système"""
    return stock_api_manager.get_stock_price(symbol, force_refresh) 