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
        """Récupère le prix via yfinance, avec retries et fallback history."""
        try:
            import yfinance as yf  # type: ignore
        except Exception as e:
            logger.warning(f"⚠️ yfinance non disponible: {e}")
            return None

        for attempt in range(3):
            try:
                logger.info(f"🔄 yfinance {symbol} (tentative {attempt+1}/3)")
                ticker = yf.Ticker(symbol)

                price = None
                change = None
                change_percent = None
                volume = None
                currency = None
                fifty_two_week_high = None
                fifty_two_week_low = None
                pe_ratio = None

                # fast_info
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

                # info
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

                # Fallback history (avec timeout si supporté)
                if price is None:
                    try:
                        try:
                            hist = ticker.history(period="1d", timeout=20)
                        except TypeError:
                            hist = ticker.history(period="1d")
                        if hist is not None and not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            if currency is None:
                                try:
                                    currency = (ticker.get_info() or {}).get('currency')
                                except Exception:
                                    pass
                    except Exception:
                        pass

                if price is None or (isinstance(price, (int, float)) and float(price) <= 0):
                    raise RuntimeError("yfinance: prix invalide ou indisponible")

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
                logger.warning(f"⚠️ yfinance échec {symbol} tentative {attempt+1}/3: {e}")
                if attempt < 2:
                    time.sleep(5)
                else:
                    return None

class StockAPIManager:
    """Gestionnaire principal des APIs boursières"""
    
    def __init__(self):
        self.alpha_vantage = AlphaVantageAPI()
        self.eodhd = EODHDAPI()
        self.finnhub = FinnhubAPI()
        self.yfinance = YFinanceAPI()
        self.fred = FredAPI()
        self.cache = {}
        # Toujours à jour: désactiver le cache par défaut
        self.cache_duration = 0
    
    def get_stock_price(self, symbol: str, force_refresh=False) -> Optional[Dict[str, Any]]:
        """
        Récupère le prix d'une action en utilisant EXCLUSIVEMENT yfinance.
        Retourne: price, change, change_percent, volume, currency, timestamp, source.
        """
        # Vérifier le cache (désactivé si cache_duration=0)
        if self.cache_duration > 0 and not force_refresh and symbol in self.cache:
            cached_data = self.cache[symbol]
            if time.time() - cached_data['timestamp'] < self.cache_duration:
                logger.info(f"📋 Données en cache pour {symbol}")
                return cached_data['data']

        logger.info(f"🔍 Récupération prix (yfinance) pour {symbol}")
        result = self.yfinance.get_stock_price(symbol)
        if result and result.get('price', 0) is not None and float(result.get('price', 0)) > 0:
            result = self._adjust_currency_for_swiss_stocks(symbol, result)
            if self.cache_duration > 0:
                self._cache_result(symbol, result)
            return result

        logger.error(f"❌ yfinance indisponible pour {symbol}")
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
            "bonds": {},
            "macros": {}
        }

        # Liste ordonnée des requêtes à effectuer (avec affichage)
        # Inclut USA, Europe (y compris Suisse), Asie (y compris Japon) et quelques sociétés phares européennes
        ordered_symbols = [
            # Actions USA (repères tech)
            ("stocks", "NVDA", "NVDA"),
            ("stocks", "MSFT", "MSFT"),
            ("stocks", "AMD", "AMD"),
            ("stocks", "AAPL", "AAPL"),
            # Actions Europe/Suisse (sociétés phares)
            ("stocks", "Nestlé (CH)", "NESN.SW"),
            ("stocks", "Novartis (CH)", "NOVN.SW"),
            ("stocks", "Roche (CH)", "ROG.SW"),
            ("stocks", "IREN (CH)", "IREN.SW"),
            ("stocks", "LVMH (FR)", "MC.PA"),
            ("stocks", "ASML (NL)", "ASML.AS"),
            # Indices USA
            ("indices", "S&P 500", "^GSPC"),
            ("indices", "NASDAQ", "^IXIC"),
            ("indices", "Dow Jones", "^DJI"),
            ("indices", "Russell 2000", "^RUT"),
            # Indices Europe
            ("indices", "Euro Stoxx 50", "^STOXX50E"),
            ("indices", "DAX", "^GDAXI"),
            ("indices", "CAC 40", "^FCHI"),
            ("indices", "FTSE 100", "^FTSE"),
            ("indices", "SMI", "^SSMI"),
            # Indices Asie
            ("indices", "Nikkei 225", "^N225"),
            ("indices", "Hang Seng", "^HSI"),
            ("indices", "Shanghai Composite", "^SSEC"),
            # Volatilité
            ("volatility", "VIX", "^VIX"),
            # Matières premières
            ("commodities", "WTI", "CL=F"),
            ("commodities", "Brent", "BZ=F"),
            ("commodities", "Natural Gas", "NG=F"),
            ("commodities", "Or (Gold)", "GC=F"),
            # Crypto
            ("crypto", "Bitcoin", "BTC-USD"),
            ("crypto", "Ethereum", "ETH-USD"),
            # Devises / Indice dollar
            ("forex", "DXY", "DX=F"),
            # Obligations US
            ("bonds", "US2Y", "^UST2Y"),
            ("bonds", "US5Y", "^FVX"),
            ("bonds", "US10Y", "^TNX"),
        ]

        # Utiliser exclusivement yfinance
        start_time = time.time()
        max_execution_time = 420  # 7 minutes max
        
        for category, display_name, symbol in ordered_symbols:
            # Vérifier le timeout global
            if time.time() - start_time > max_execution_time:
                logger.warning(f"⚠️ Timeout global atteint ({max_execution_time}s), arrêt de la récupération")
                break
            # Obligations: utiliser FRED en priorité
            if category == 'bonds' and display_name in ('US10Y','US5Y','US2Y'):
                series_map = {'US2Y': 'DGS2', 'US5Y': 'DGS5', 'US10Y': 'DGS10'}
                series_id = series_map.get(display_name)
                fred_res = self.fred.get_latest_yield(series_id) if series_id else None
                if fred_res:
                    snapshot[category][display_name] = fred_res
                else:
                    # Si FRED échoue pour les bonds, mettre N/A au lieu d'essayer yfinance
                    logger.warning(f"⚠️ FRED indisponible pour {display_name}, mise à N/A")
                    snapshot[category][display_name] = {
                        'yield': 'N/A',
                        'change_bps': 'N/A',
                        'source': 'FRED (indisponible)'
                    }
                continue  # Ne pas essayer yfinance pour les bonds
            
            # Pour tous les autres actifs, utiliser yfinance
            try:
                logger.info(f"⏳ Attente 11s avant la requête yfinance pour {symbol} ({display_name})...")
                time.sleep(11)
                logger.info(f"🔄 Récupération yfinance pour {symbol} ({display_name})...")
                data = self.yfinance.get_stock_price(symbol)
                if data and data.get('price') is not None:
                    if category == 'forex' and display_name == 'DXY':
                        snapshot[category][display_name] = {
                            "value": data.get('price'),
                            "change": data.get('change'),
                            "change_percent": data.get('change_percent'),
                            "source": data.get('source')
                        }
                    else:
                        snapshot[category][display_name] = {"price": data.get('price'), "change": data.get('change'), "change_percent": data.get('change_percent'), "source": data.get('source')}
                else:
                    snapshot[category][display_name] = {"error": "Data not available"}
            except Exception as e:
                logger.warning(f"⚠️ Erreur pour {symbol} ({display_name}): {e}")
                snapshot[category][display_name] = {"error": f"Error: {str(e)}"}
                continue  # Continuer avec le prochain symbole

        # Calculs dérivés (analytics)
        analytics: Dict[str, Any] = {}

        # Gold/Silver ratio
        try:
            gold = snapshot.get('commodities', {}).get('Or (Gold)', {}).get('price')
            # Ajouter Silver si absent
            if 'Silver' not in snapshot.get('commodities', {}):
                try:
                    logger.info("⏳ Attente 11s avant la requête yfinance pour SI=F (Silver)...")
                    time.sleep(11)
                    logger.info("🔄 Récupération Silver (SI=F) via yfinance...")
                    silver_data = self.yfinance.get_stock_price('SI=F')
                    snapshot['commodities']['Silver'] = {
                        'price': silver_data.get('price') if silver_data else None,
                        'change': silver_data.get('change') if silver_data else None,
                        'change_percent': silver_data.get('change_percent') if silver_data else None,
                        'source': (silver_data or {}).get('source') if silver_data else None
                    }
                except Exception as e:
                    logger.warning(f"⚠️ Erreur récupération Silver: {e}")
                    snapshot['commodities']['Silver'] = {
                        'price': None,
                        'change': None,
                        'change_percent': None,
                        'source': 'Error'
                    }
            silver = snapshot.get('commodities', {}).get('Silver', {}).get('price')
            if gold and silver and silver != 0:
                analytics['gold_silver_ratio'] = round(float(gold) / float(silver), 2)
        except Exception as e:
            logger.warning(f"⚠️ Impossible de calculer le ratio Or/Argent: {e}")

        # Courbe 2-10Y
        try:
            ten_y = snapshot.get('bonds', {}).get('US 10Y', {}).get('yield')
            two_y = snapshot.get('bonds', {}).get('US 2Y', {}).get('yield')
            if isinstance(ten_y, (int, float)) and isinstance(two_y, (int, float)):
                analytics['spread_2_10_bps'] = round((float(ten_y) - float(two_y)) * 100.0, 1)
        except Exception as e:
            logger.warning(f"⚠️ Impossible de calculer le spread 2-10Y: {e}")

        # RSI(14) sur S&P 500 (^GSPC)
        try:
            rsi = self._get_yfinance_rsi('^GSPC', period=14)
            if rsi is not None:
                analytics['rsi_spx_14'] = round(rsi, 1)
        except Exception as e:
            logger.warning(f"⚠️ RSI SPX indisponible: {e}")

        # Crypto Fear & Greed (Alternative.me)
        try:
            analytics['btc_fear_greed'] = self._get_crypto_fng()
        except Exception as e:
            logger.warning(f"⚠️ Fear&Greed indisponible: {e}")

        # BTC Dominance (CoinGecko)
        try:
            analytics['btc_dominance_pct'] = self._get_btc_dominance_pct()
        except Exception as e:
            logger.warning(f"⚠️ BTC dominance indisponible: {e}")

        # VIX régime
        try:
            vix = snapshot.get('volatility', {}).get('VIX', {}).get('price')
            if isinstance(vix, (int, float)):
                regime = 'Crisis (>30)'
                if vix < 15: regime = 'Low (<15)'
                elif vix < 20: regime = 'Normal (15-20)'
                elif vix < 30: regime = 'Elevated (20-30)'
                analytics['vix_regime'] = regime
        except Exception:
            pass

        # Market phase (US)
        try:
            now_utc = datetime.utcnow()
            wd = now_utc.weekday()
            hour = now_utc.hour
            minute = now_utc.minute
            # Approximation: Marchés US ouverts ~ 13:30-20:00 UTC (selon DST)
            trading = (hour > 13 or (hour == 13 and minute >= 30)) and (hour < 20)
            weekend = wd >= 5
            phase = 'Weekend' if weekend else ('Trading' if trading else ('Pre-market' if hour < 13 else 'After-hours'))
            analytics['market_phase'] = phase
        except Exception:
            pass

        snapshot['analytics'] = analytics
        
        # Ajout: Indicateurs macro FRED (groupés par thèmes)
        try:
            fred_blocks = {
                'rates_yields': {
                    # US
                    'DFF': "Fed Funds Rate",
                    'DGS2': "2Y Treasury",
                    'DGS10': "10Y Treasury",
                    'DGS30': "30Y Treasury",
                    'T10Y2Y': "Yield Curve 10Y-2Y",
                    'BAMLH0A0HYM2': "High Yield Spread",
                    # Europe
                    'IRLTLT01EZM156N': "ECB 10Y",
                    'IR3TIB01DEM156N': "3M Euribor",
                    # Suisse
                    'IRLTLT01CHM156N': "Swiss 10Y",
                    'IRSTCI01CHM156N': "SARON",
                },
                'inflation': {
                    'CPIAUCSL': "US CPI",
                    'CPILFESL': "US Core CPI",
                    'PCEPI': "US PCE",
                    'DPCCRV1Q225SBEA': "US Core PCE",
                    'CP0000EZ19M086NEST': "Eurozone HICP",
                    'CPALTT01CHM659N': "Swiss CPI",
                },
                'employment': {
                    'UNRATE': "US Unemployment",
                    'PAYEMS': "US NFP",
                    'CIVPART': "US Participation Rate",
                    'EMVOVERALLEMV': "US Job Openings",
                    'LRHUTTTTEZM156S': "Eurozone Unemployment",
                },
                'activity': {
                    'GDP': "US GDP",
                    'GDPC1': "US Real GDP",
                    'MANEMP': "ISM Manufacturing",
                    'NMFBAI': "ISM Services",
                    'RSAFS': "US Retail Sales",
                    'INDPRO': "US Industrial Production",
                    'NAPM': "US PMI Composite",
                },
                'liquidity_stress': {
                    'WALCL': "Fed Balance Sheet",
                    'RRPONTSYD': "Reverse Repo",
                    'SOFR': "SOFR Rate",
                    'TEDRATE': "TED Spread",
                    'DCOILWTICO': "WTI Oil",
                    'DEXUSEU': "EUR/USD",
                }
            }
            # Formatage/Unités par série FRED
            def _fred_series_format(series_id: str) -> Dict[str, Any]:
                """Retourne unit, change_unit, scale d'affichage (pour value), et decimals.
                - unit: suffixe d'unité pour la valeur (ex: '%', 'index', 'bln USD', 'USD/bbl', 'ratio', 'K jobs')
                - change_unit: unité de variation (ex: 'bp', 'pp', 'pts', 'USD')
                - scale: facteur à appliquer à la valeur brute pour l'affichage
                - decimals: nombre de décimales recommandé
                """
                percent_series = {
                    'DFF','DGS2','DGS10','DGS30','T10Y2Y','BAMLH0A0HYM2',
                    'IRLTLT01EZM156N','IR3TIB01DEM156N','IRLTLT01CHM156N','IRSTCI01CHM156N',
                    'UNRATE','CIVPART','SOFR','TEDRATE'
                }
                index_series = {
                    'CPIAUCSL','CPILFESL','PCEPI','DPCCRV1Q225SBEA','CP0000EZ19M086NEST','CPALTT01CHM659N',
                    'INDPRO','NAPM','NMFBAI'
                }
                usd_per_barrel = {'DCOILWTICO'}
                ratio_series = {'DEXUSEU'}
                bln_usd_series = {'GDP','GDPC1'}  # déjà en milliards
                mln_to_bln_series = {'WALCL','RRPONTSYD','RSAFS'}  # millions -> milliards
                k_jobs_series = {'PAYEMS'}  # milliers de personnes

                if series_id in percent_series:
                    # Valeur en %, variation en points de pourcentage (pp); pour DGS*, change est en bp
                    if series_id in {'DGS2','DGS10','DGS30'}:
                        return {'unit': '%', 'change_unit': 'bp', 'scale': 1.0, 'decimals': 2}
                    return {'unit': '%', 'change_unit': 'pp', 'scale': 1.0, 'decimals': 2}
                if series_id in index_series:
                    return {'unit': 'index', 'change_unit': 'pts', 'scale': 1.0, 'decimals': 1}
                if series_id in usd_per_barrel:
                    return {'unit': 'USD/bbl', 'change_unit': 'USD', 'scale': 1.0, 'decimals': 2}
                if series_id in ratio_series:
                    return {'unit': 'ratio', 'change_unit': None, 'scale': 1.0, 'decimals': 4}
                if series_id in bln_usd_series:
                    return {'unit': 'bln USD', 'change_unit': 'bln USD', 'scale': 1.0, 'decimals': 1}
                if series_id in mln_to_bln_series:
                    return {'unit': 'bln USD', 'change_unit': 'bln USD', 'scale': 1e-3, 'decimals': 1}
                if series_id in k_jobs_series:
                    return {'unit': 'K jobs', 'change_unit': 'K', 'scale': 1.0, 'decimals': 0}
                # Défaut
                return {'unit': None, 'change_unit': None, 'scale': 1.0, 'decimals': 2}

            macros: Dict[str, Any] = {}
            for block, series in fred_blocks.items():
                macros[block] = {}
                for sid, label in series.items():
                    # Yields: privilégier get_latest_yield pour tranches reconnues
                    val = None
                    if sid in ('DGS2','DGS10','DGS30'):
                        val = self.fred.get_latest_yield(sid)
                        if val is not None and 'yield' in val:
                            fmt = _fred_series_format(sid)
                            macros[block][label] = {
                                "value": val['yield'],
                                "change": val.get('change_bps'),
                                "unit": fmt.get('unit'),
                                "change_unit": fmt.get('change_unit'),
                                "scale": fmt.get('scale'),
                                "decimals": fmt.get('decimals'),
                                "source": val.get('source')
                            }
                            try:
                                logger.debug(f"FRED {block}/{label} ({sid}) -> yield={val['yield']}, change_bps={val.get('change_bps')}")
                            except Exception:
                                pass
                            continue
                    # Autres séries: valeur simple
                    v = self.fred.get_latest_value(sid)
                    if v is not None:
                        fmt = _fred_series_format(sid)
                        macros[block][label] = {
                            "value": v.get('value'),
                            "change": v.get('change'),
                            "unit": fmt.get('unit'),
                            "change_unit": fmt.get('change_unit'),
                            "scale": fmt.get('scale'),
                            "decimals": fmt.get('decimals'),
                            "source": v.get('source')
                        }
                        try:
                            logger.debug(f"FRED {block}/{label} ({sid}) -> value={v.get('value')}, change={v.get('change')}")
                        except Exception:
                            pass
                    else:
                        try:
                            logger.debug(f"FRED {block}/{label} ({sid}) -> aucune donnée")
                        except Exception:
                            pass
            snapshot['macros'] = macros
        except Exception as e:
            logger.warning(f"⚠️ Indicateurs FRED non disponibles: {e}")
        
        execution_time = time.time() - start_time
        logger.info(f"✅ Aperçu du marché (strict) récupéré en {execution_time:.1f}s")
        return snapshot

    def _get_yfinance_rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        """Calcule le RSI(period) via yfinance (données journalières)."""
        try:
            logger.info(f"🔄 Calcul RSI pour {symbol} (period={period})...")
            import yfinance as yf  # type: ignore
            import pandas as pd  # type: ignore
            
            # Timeout plus court et retry intelligent
            for attempt in range(2):
                try:
                    hist = yf.download(symbol, period='6mo', interval='1d', progress=False, auto_adjust=True, timeout=15)
                    if hist is None or hist.empty or 'Close' not in hist:
                        logger.warning(f"⚠️ Données yfinance vides pour {symbol}")
                        return None
                    
                    close = hist['Close']
                    delta = close.diff()
                    gain = delta.clip(lower=0)
                    loss = -delta.clip(upper=0)
                    avg_gain = gain.rolling(window=period, min_periods=period).mean()
                    avg_loss = loss.rolling(window=period, min_periods=period).mean()
                    rs = (avg_gain / avg_loss).replace([float('inf'), -float('inf')], 0)
                    rsi = 100 - (100 / (1 + rs))
                    val = float(rsi.iloc[-1]) if not rsi.empty else None
                    
                    if val is not None:
                        logger.info(f"✅ RSI calculé pour {symbol}: {val:.1f}")
                        return val
                    else:
                        logger.warning(f"⚠️ RSI non calculable pour {symbol}")
                        return None
                        
                except Exception as e:
                    if attempt < 1:
                        logger.warning(f"⚠️ Tentative {attempt+1} échouée pour {symbol}, retry...")
                        time.sleep(2)  # Délai court pour retry
                        continue
                    else:
                        logger.warning(f"⚠️ RSI indisponible pour {symbol}: {e}")
                        return None
                        
        except Exception as e:
            logger.warning(f"⚠️ RSI indisponible pour {symbol}: {e}")
            return None

    def _get_crypto_fng(self) -> Optional[int]:
        """Crypto Fear & Greed Index (Alternative.me) value 0-100."""
        try:
            logger.info("🔄 Récupération Crypto Fear & Greed Index...")
            url = 'https://api.alternative.me/fng/?limit=1&format=json'
            
            # Gestion intelligente des erreurs avec délais progressifs
            for attempt in range(3):
                try:
                    # Délai progressif pour éviter le rate limiting
                    if attempt > 0:
                        delay = 3 * attempt  # 3s, 6s, 9s
                        logger.info(f"⏳ Attente {delay}s avant tentative {attempt+1}...")
                        time.sleep(delay)
                    
                    resp = requests.get(url, timeout=10)
                    
                    # Gestion spécifique de l'erreur 429 (Too Many Requests)
                    if resp.status_code == 429:
                        if attempt < 2:
                            logger.warning(f"⚠️ Rate limit atteint (429), tentative {attempt+1} dans {3 * (attempt+1)}s...")
                            continue
                        else:
                            logger.warning("⚠️ Crypto FNG indisponible: Rate limit persistant après 3 tentatives")
                            return None
                    
                    resp.raise_for_status()
                    data = resp.json()
                    val = int(data['data'][0]['value'])
                    
                    if 0 <= val <= 100:
                        logger.info(f"✅ Crypto FNG récupéré: {val}")
                        return val
                    else:
                        logger.warning(f"⚠️ Valeur FNG invalide: {val}")
                        return None
                        
                except requests.exceptions.HTTPError as e:
                    if attempt < 2:
                        logger.warning(f"⚠️ Tentative {attempt+1} FNG échouée (HTTP {e.response.status_code}), retry...")
                        continue
                    else:
                        logger.warning(f"⚠️ Crypto FNG indisponible: {e}")
                        return None
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"⚠️ Tentative {attempt+1} FNG échouée, retry...")
                        continue
                    else:
                        logger.warning(f"⚠️ Crypto FNG indisponible: {e}")
                        return None
                        
        except Exception as e:
            logger.warning(f"⚠️ Crypto FNG indisponible: {e}")
            return None

    def _get_btc_dominance_pct(self) -> Optional[float]:
        """BTC dominance percentage via CoinGecko global endpoint."""
        try:
            logger.info("🔄 Récupération BTC dominance...")
            url = 'https://api.coingecko.com/api/v3/global'
            
            # Gestion intelligente du rate limiting avec délais progressifs
            for attempt in range(3):
                try:
                    # Délai progressif pour éviter le rate limiting
                    if attempt > 0:
                        delay = 5 * attempt  # 5s, 10s, 15s
                        logger.info(f"⏳ Attente {delay}s avant tentative {attempt+1}...")
                        time.sleep(delay)
                    
                    resp = requests.get(url, timeout=10)
                    
                    # Gestion spécifique de l'erreur 429 (Too Many Requests)
                    if resp.status_code == 429:
                        if attempt < 2:
                            logger.warning(f"⚠️ Rate limit atteint (429), tentative {attempt+1} dans {5 * (attempt+1)}s...")
                            continue
                        else:
                            logger.warning("⚠️ BTC dominance indisponible: Rate limit persistant après 3 tentatives")
                            return None
                    
                    resp.raise_for_status()
                    data = resp.json()
                    pct = float(data['data']['market_cap_percentage']['btc'])
                    
                    if 0 <= pct <= 100:
                        rounded_pct = round(pct, 2)
                        logger.info(f"✅ BTC dominance récupéré: {rounded_pct}%")
                        return rounded_pct
                    else:
                        logger.warning(f"⚠️ Valeur BTC dominance invalide: {pct}%")
                        return None
                        
                except requests.exceptions.HTTPError as e:
                    if attempt < 2:
                        logger.warning(f"⚠️ Tentative {attempt+1} BTC dominance échouée (HTTP {e.response.status_code}), retry...")
                        continue
                    else:
                        logger.warning(f"⚠️ BTC dominance indisponible: {e}")
                        return None
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"⚠️ Tentative {attempt+1} BTC dominance échouée, retry...")
                        continue
                    else:
                        logger.warning(f"⚠️ BTC dominance indisponible: {e}")
                        return None
                        
        except Exception as e:
            logger.warning(f"⚠️ BTC dominance indisponible: {e}")
            return None

class FredAPI:
    """FRED (Federal Reserve) simple client pour rendements US."""
    def __init__(self):
        self.api_key = os.environ.get('FRED_API_KEY')
        self.base = 'https://api.stlouisfed.org/fred/series/observations'

    @rate_limit(calls_per_minute=12)
    def get_latest_yield(self, series_id: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        try:
            import requests
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 10
            }
            r = requests.get(self.base, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            obs = [o for o in (data.get('observations') or []) if o.get('value') not in (None, '.', '')]
            if not obs:
                return None
            latest = float(obs[0]['value'])
            change_bps = None
            if len(obs) > 1:
                try:
                    prev = float(obs[1]['value'])
                    change_bps = round((latest - prev) * 100.0, 1)
                except Exception:
                    change_bps = None
            return {"yield": round(latest, 3), "change_bps": change_bps, "source": 'FRED'}
        except Exception:
            return None

    @rate_limit(calls_per_minute=12)
    def get_latest_value(self, series_id: str) -> Optional[Dict[str, Any]]:
        """Retourne la dernière valeur numérique d'une série FRED (valeur et variation d'une obs)."""
        if not self.api_key:
            return None
        try:
            import requests
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 10
            }
            r = requests.get(self.base, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            obs = [o for o in (data.get('observations') or []) if o.get('value') not in (None, '.', '')]
            if not obs:
                return None
            latest = float(obs[0]['value'])
            change = None
            if len(obs) > 1:
                try:
                    prev = float(obs[1]['value'])
                    change = round(latest - prev, 4)
                except Exception:
                    change = None
            return {"value": latest, "change": change, "source": 'FRED'}
        except Exception:
            return None


# Instance globale
stock_api_manager = StockAPIManager()

# Fonctions de compatibilité
def get_stock_price_stable(symbol: str) -> Optional[Dict[str, Any]]:
    """Fonction de compatibilité avec l'ancien système"""
    return stock_api_manager.get_stock_price(symbol)

def get_stock_price_manus(symbol: str, item=None, cache_key=None, force_refresh=False) -> Optional[Dict[str, Any]]:
    """Fonction de compatibilité avec l'ancien système"""
    return stock_api_manager.get_stock_price(symbol, force_refresh) 