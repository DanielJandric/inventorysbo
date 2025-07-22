#!/usr/bin/env python3
"""
Intégration des APIs Manus pour remplacer toutes les autres APIs
- API de cours de bourse: https://ogh5izcelen1.manus.space/
- API de rapports de marché: https://y0h0i3cqzyko.manus.space/api/report
"""

import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManusStockAPI:
    """API Manus pour les cours de bourse - Remplace toutes les autres APIs de prix"""
    
    def __init__(self):
        self.base_url = "https://ogh5izcelen1.manus.space"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InventorySBO/1.0 (Manus Integration)'
        })
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_stock_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Récupère le prix d'une action via l'API Manus"""
        cache_key = f"stock_{symbol}"
        
        # Vérifier le cache
        if not force_refresh and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return cached_data
        
        try:
            # Essayer différents endpoints
            endpoints = [
                f"/api/stocks/{symbol}",
                f"/stocks/{symbol}",
                f"/api/prices/{symbol}",
                f"/prices/{symbol}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        # Parser le HTML pour extraire les données
                        html_content = response.text
                        parsed_data = self._parse_html_content(html_content, symbol)
                        
                        # Données disponibles via l'API Manus
                        stock_data = {
                            'symbol': symbol,
                            'name': parsed_data.get('name', symbol),
                            'price': parsed_data.get('price'),
                            'change': parsed_data.get('change'),
                            'change_percent': parsed_data.get('change_percent'),
                            'volume': parsed_data.get('volume'),
                            'market_cap': parsed_data.get('market_cap'),
                            'pe_ratio': parsed_data.get('pe_ratio'),
                            'high_52_week': parsed_data.get('high_52_week'),
                            'low_52_week': parsed_data.get('low_52_week'),
                            'open': parsed_data.get('open'),
                            'previous_close': parsed_data.get('previous_close'),
                            'currency': parsed_data.get('currency', 'USD'),
                            'exchange': parsed_data.get('exchange', 'NASDAQ'),
                            'last_updated': datetime.now().isoformat(),
                            'source': 'Manus API',
                            'status': 'available',
                            'endpoint': endpoint,
                            'raw_content_length': len(response.text),
                            'parsing_success': parsed_data.get('parsing_success', False)
                        }
                        
                        # Mettre en cache
                        self.cache[cache_key] = (stock_data, datetime.now())
                        
                        # Si le parsing a échoué, essayer le fallback
                        if not stock_data.get('parsing_success', False):
                            logger.info(f"🔄 Parsing Manus échoué pour {symbol}, tentative de fallback...")
                            fallback_data = self._try_fallback_api(symbol)
                            if fallback_data:
                                # Mettre à jour le cache avec les données de fallback
                                self.cache[cache_key] = (fallback_data, datetime.now())
                                return fallback_data
                            else:
                                # Si le fallback échoue aussi, retourner les données Manus mais avec un avertissement
                                logger.warning(f"⚠️ Fallback échoué pour {symbol}, retour des données Manus (prix peut être incorrect)")
                                return stock_data
                        
                        return stock_data
                        
                except Exception as e:
                    logger.debug(f"Erreur endpoint {endpoint}: {e}")
                    continue
            
            # Données par défaut si aucun endpoint ne fonctionne
            default_data = {
                'symbol': symbol,
                'name': symbol,
                'price': None,
                'change': None,
                'change_percent': None,
                'volume': None,
                'market_cap': None,
                'pe_ratio': None,
                'high_52_week': None,
                'low_52_week': None,
                'open': None,
                'previous_close': None,
                'currency': self._get_currency_for_symbol(symbol, {}),
                'exchange': 'NASDAQ',
                'last_updated': datetime.now().isoformat(),
                'source': 'Manus API',
                'status': 'unavailable',
                'error': 'API non disponible'
            }
            
            self.cache[cache_key] = (default_data, datetime.now())
            
            # Essayer un fallback vers une API alternative
            fallback_data = self._try_fallback_api(symbol)
            if fallback_data:
                return fallback_data
            
            return default_data
            
        except Exception as e:
            logger.error(f"Erreur récupération prix {symbol}: {e}")
            return {
                'symbol': symbol,
                'status': 'error',
                'error': str(e),
                'currency': self._get_currency_for_symbol(symbol, {}),
                'last_updated': datetime.now().isoformat()
            }
    
    def _parse_html_content(self, html_content: str, symbol: str) -> Dict[str, Any]:
        """Parse le contenu HTML pour extraire les données boursières"""
        try:
            # Patterns pour extraire les données
            patterns = {
                'price': [
                    r'price["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
                    r'current-price["\']?\s*:\s*["\']?([\d,]+\.?\d*)["\']?',
                    r'[\$€£]?\s*([\d,]+\.?\d*)\s*USD?',
                    r'price["\']?\s*=\s*["\']?([\d,]+\.?\d*)["\']?'
                ],
                'change': [
                    r'change["\']?\s*:\s*["\']?([+-]?[\d,]+\.?\d*)["\']?',
                    r'[\$€£]?\s*([+-]?[\d,]+\.?\d*)\s*\([+-]?\d+\.?\d*%\)'
                ],
                'change_percent': [
                    r'change-percent["\']?\s*:\s*["\']?([+-]?\d+\.?\d*)%["\']?',
                    r'\(([+-]?\d+\.?\d*)%\)',
                    r'[\$€£]?\s*[+-]?[\d,]+\.?\d*\s*\(([+-]?\d+\.?\d*)%\)'
                ],
                'volume': [
                    r'volume["\']?\s*:\s*["\']?([\d,]+)["\']?',
                    r'volume["\']?\s*=\s*["\']?([\d,]+)["\']?'
                ],
                'market_cap': [
                    r'market-cap["\']?\s*:\s*["\']?([\d,]+\.?\d*[MBK]?)["\']?',
                    r'marketcap["\']?\s*:\s*["\']?([\d,]+\.?\d*[MBK]?)["\']?'
                ]
            }
            
            parsed_data = {
                'name': symbol,
                'price': None,
                'change': None,
                'change_percent': None,
                'volume': None,
                'market_cap': None,
                'pe_ratio': None,
                'high_52_week': None,
                'low_52_week': None,
                'open': None,
                'previous_close': None,
                'currency': self._get_currency_for_symbol(symbol, {}),
                'exchange': 'NASDAQ',
                'parsing_success': False
            }
            
            # Essayer d'extraire chaque donnée
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        try:
                            value = match.group(1).replace(',', '')
                            if field == 'price':
                                parsed_data[field] = float(value)
                            elif field in ['change', 'change_percent']:
                                parsed_data[field] = float(value)
                            elif field == 'volume':
                                parsed_data[field] = int(value)
                            else:
                                parsed_data[field] = value
                            break
                        except (ValueError, AttributeError):
                            continue
            
            # Marquer comme succès si au moins le prix est trouvé ET qu'il n'est pas 1.0
            if parsed_data['price'] is not None and parsed_data['price'] != 1.0:
                parsed_data['parsing_success'] = True
                # Déterminer la devise correcte même pour les données Manus
                correct_currency = self._get_currency_for_symbol(symbol, {})
                parsed_data['currency'] = correct_currency
                logger.info(f"✅ Parsing HTML réussi pour {symbol}: prix={parsed_data['price']} {correct_currency}")
            else:
                parsed_data['parsing_success'] = False
                if parsed_data['price'] == 1.0:
                    logger.warning(f"⚠️ Parsing HTML incorrect pour {symbol}: prix=1.0 (pattern générique)")
                else:
                    logger.warning(f"⚠️ Parsing HTML échoué pour {symbol}, aucun prix trouvé")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing HTML pour {symbol}: {e}")
            return {
                'name': symbol,
                'price': None,
                'currency': self._get_currency_for_symbol(symbol, {}),
                'parsing_success': False
            }
    
    def _try_fallback_api(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Essaie une API de fallback si Manus échoue"""
        try:
            # Essayer yfinance en premier (gratuit et fiable)
            return self._try_yfinance_fallback(symbol)
            
        except Exception as e:
            logger.error(f"❌ Erreur fallback API pour {symbol}: {e}")
            return None
    
    def _try_yfinance_fallback(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fallback vers yfinance"""
        try:
            import yfinance as yf
            
            logger.info(f"🔄 Tentative fallback yfinance pour {symbol}")
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Obtenir la devise correcte pour ce symbole
            correct_currency = self._get_currency_for_symbol(symbol, info)
            
            # Extraire les données importantes
            price_data = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'price': info.get('currentPrice'),
                'change': info.get('regularMarketChange'),
                'change_percent': info.get('regularMarketChangePercent'),
                'volume': info.get('volume'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'high_52_week': info.get('fiftyTwoWeekHigh'),
                'low_52_week': info.get('fiftyTwoWeekLow'),
                'open': info.get('regularMarketOpen'),
                'previous_close': info.get('regularMarketPreviousClose'),
                'currency': correct_currency,
                'exchange': info.get('exchange', 'NASDAQ'),
                'last_updated': datetime.now().isoformat(),
                'source': 'Yahoo Finance (yfinance)',
                'status': 'fallback_success',
                'fallback_reason': 'Manus API parsing failed'
            }
            
            if price_data['price']:
                logger.info(f"✅ Fallback yfinance réussi pour {symbol}: {price_data['price']} {price_data['currency']}")
                return price_data
            else:
                logger.warning(f"⚠️ Fallback yfinance échoué pour {symbol}: prix non disponible")
                return None
                
        except ImportError:
            logger.warning("⚠️ yfinance non installé, fallback non disponible")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur fallback yfinance pour {symbol}: {e}")
            return None
    
    def _get_currency_for_symbol(self, symbol: str, yf_info: Dict[str, Any]) -> str:
        """Détermine la devise correcte pour un symbole"""
        # Mapping des devises par symbole
        currency_map = {
            # Actions américaines
            "AAPL": "USD",
            "TSLA": "USD", 
            "MSFT": "USD",
            "GOOGL": "USD",
            "MPW": "USD",
            "AMZN": "USD",
            "META": "USD",
            "NVDA": "USD",
            "NFLX": "USD",
            
            # Actions suisses (.SW)
            "IREN.SW": "CHF",
            "NOVN.SW": "CHF",
            "ROG.SW": "CHF",
            "NESN.SW": "CHF",
            "UHR.SW": "CHF",
            "CSGN.SW": "CHF",
            "UBSG.SW": "CHF",
            "ABBN.SW": "CHF",
            "LONN.SW": "CHF",
            "GIVN.SW": "CHF",
            
            # Actions européennes
            "ASML": "EUR",
            "SAP": "EUR",
            "BMW": "EUR",
            "VOW3": "EUR",
            "SIE": "EUR",
            "BAYN": "EUR",
            "BAS": "EUR",
            
            # Actions britanniques
            "HSBA": "GBP",
            "BP": "GBP",
            "GSK": "GBP",
            "VOD": "GBP",
            "RIO": "GBP",
            "BHP": "GBP"
        }
        
        # Vérifier d'abord le mapping explicite
        if symbol in currency_map:
            logger.info(f"💰 Devise mappée pour {symbol}: {currency_map[symbol]}")
            return currency_map[symbol]
        
        # Vérifier la devise retournée par yfinance
        yf_currency = yf_info.get('currency')
        if yf_currency and yf_currency in ['USD', 'CHF', 'EUR', 'GBP']:
            logger.info(f"💰 Devise yfinance pour {symbol}: {yf_currency}")
            return yf_currency
        
        # Vérifier l'exchange pour déduire la devise
        exchange = yf_info.get('exchange', '').upper()
        if 'SW' in exchange or '.SW' in symbol:
            logger.info(f"💰 Devise déduite (Suisse) pour {symbol}: CHF")
            return "CHF"
        elif exchange in ['LSE', 'LON']:
            logger.info(f"💰 Devise déduite (UK) pour {symbol}: GBP")
            return "GBP"
        elif exchange in ['FRA', 'ETR', 'AMS']:
            logger.info(f"💰 Devise déduite (Europe) pour {symbol}: EUR")
            return "EUR"
        elif exchange in ['NMS', 'NYQ', 'ASE']:
            logger.info(f"💰 Devise déduite (US) pour {symbol}: USD")
            return "USD"
        
        # Par défaut, utiliser USD
        logger.warning(f"⚠️ Devise par défaut pour {symbol}: USD")
        return "USD"
    
    def get_multiple_stock_prices(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Récupère les prix de plusieurs actions"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_price(symbol, force_refresh)
        return results
    
    def clear_cache(self) -> Dict[str, Any]:
        """Vide le cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        return {
            'status': 'success',
            'cache_cleared': True,
            'entries_removed': cache_size,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retourne le statut du cache"""
        return {
            'cache_size': len(self.cache),
            'cache_duration_seconds': self.cache_duration,
            'cached_symbols': list(self.cache.keys()),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_api_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'API"""
        try:
            # Test simple de l'API
            test_symbol = "AAPL"
            test_data = self.get_stock_price(test_symbol, force_refresh=True)
            
            return {
                'status': 'available',
                'api_url': self.base_url,
                'test_symbol': test_symbol,
                'test_result': 'success' if test_data.get('status') != 'unavailable' else 'failed',
                'last_checked': datetime.now().isoformat(),
                'cache_size': len(self.cache)
            }
        except Exception as e:
            return {
                'status': 'unavailable',
                'api_url': self.base_url,
                'error': str(e),
                'last_checked': datetime.now().isoformat(),
                'cache_size': len(self.cache)
            }

class ManusMarketReportAPI:
    """API Manus pour les rapports de marché - Remplace toutes les autres APIs de rapports"""
    
    def __init__(self):
        self.base_url = "https://y0h0i3cqzyko.manus.space"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InventorySBO/1.0 (Manus Integration)'
        })
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
    
    def get_market_report(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Récupère le rapport de marché via l'API Manus"""
        cache_key = "market_report"
        
        # Vérifier le cache
        if not force_refresh and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return cached_data
        
        try:
            response = self.session.get(f"{self.base_url}/api/report", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Nouvelle structure de l'API Manus
                report = data.get('report', {})
                
                # Transformer les données
                market_report = {
                    'timestamp': datetime.now().isoformat(),
                    'report_date': data.get('api_call_timestamp', datetime.now().isoformat()),
                    'generation_time': data.get('generation_time', ''),
                    'source': 'Manus API',
                    'status': 'complete',
                    
                    # Métriques de marché
                    'market_metrics': report.get('key_metrics', {}),
                    
                    # Contenu - nouvelle structure
                    'content': {
                        'html': report.get('content', {}).get('html', ''),
                        'markdown': report.get('content', {}).get('markdown', '')
                    },
                    
                    # Résumé
                    'summary': report.get('summary', {}),
                    
                    # Sections
                    'sections': report.get('metadata', {}).get('sections', []),
                    
                    # Données brutes
                    'raw_data': data
                }
                
                # Mettre en cache
                self.cache[cache_key] = (market_report, datetime.now())
                return market_report
                
            else:
                return self._create_default_report()
                
        except Exception as e:
            logger.error(f"Erreur récupération rapport: {e}")
            return self._create_default_report()
    
    def _create_default_report(self) -> Dict[str, Any]:
        """Crée un rapport par défaut"""
        return {
            'timestamp': datetime.now().isoformat(),
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'source': 'Manus API',
            'status': 'unavailable',
            'error': 'API non disponible',
            'market_metrics': {},
            'content': {},
            'summary': {},
            'sections': []
        }
    
    def generate_market_briefing(self) -> Dict[str, Any]:
        """Génère un briefing de marché"""
        try:
            market_report = self.get_market_report()
            
            if market_report.get('status') == 'complete':
                return {
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Manus API',
                    'briefing': {
                        'title': f"Briefing de Marché - {market_report.get('report_date', 'Date inconnue')}",
                        'summary': market_report.get('summary', {}).get('key_points', []),
                        'metrics': market_report.get('market_metrics', {}),
                        'content': market_report.get('content', {}).get('markdown', '')
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Impossible de récupérer les données de marché',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Vide le cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        return {
            'status': 'success',
            'cache_cleared': True,
            'entries_removed': cache_size,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retourne le statut du cache"""
        cache_entries = list(self.cache.keys())
        cache_info = {}
        
        for key in cache_entries:
            if key in self.cache:
                data, timestamp = self.cache[key]
                age = (datetime.now() - timestamp).total_seconds()
                cache_info[key] = {
                    'age_seconds': age,
                    'age_minutes': age / 60,
                    'expires_in': max(0, self.cache_duration - age)
                }
        
        return {
            'status': 'success',
            'cache_size': len(self.cache),
            'cache_duration': self.cache_duration,
            'entries': cache_info,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_api_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'API"""
        try:
            # Test simple de l'API
            test_data = self.get_market_report(force_refresh=True)
            
            return {
                'status': 'available',
                'api_url': self.base_url,
                'test_result': 'success' if test_data.get('status') == 'complete' else 'failed',
                'last_checked': datetime.now().isoformat(),
                'cache_size': len(self.cache)
            }
        except Exception as e:
            return {
                'status': 'unavailable',
                'api_url': self.base_url,
                'error': str(e),
                'last_checked': datetime.now().isoformat(),
                'cache_size': len(self.cache)
            }

# Instances globales pour remplacer les APIs existantes
manus_stock_api = ManusStockAPI()
manus_market_report_api = ManusMarketReportAPI()

# Fonctions de remplacement pour compatibilité
def get_stock_price_manus(symbol: str, item=None, cache_key=None, force_refresh: bool = False) -> Dict[str, Any]:
    """Remplace toutes les autres fonctions de prix d'actions"""
    return manus_stock_api.get_stock_price(symbol, force_refresh)

def get_market_report_manus(force_refresh: bool = False) -> Dict[str, Any]:
    """Remplace toutes les autres fonctions de rapports de marché"""
    return manus_market_report_api.get_market_report(force_refresh)

def generate_market_briefing_manus() -> Dict[str, Any]:
    """Remplace toutes les autres fonctions de briefing"""
    return manus_market_report_api.generate_market_briefing()

def get_exchange_rate_manus(from_currency: str, to_currency: str = 'CHF') -> float:
    """Récupère le taux de change via les données Manus"""
    try:
        market_report = manus_market_report_api.get_market_report()
        
        if market_report.get('status') == 'complete':
            content = market_report.get('content', {}).get('text', '')
            
            # Chercher les taux CHF dans le contenu
            if 'CHF/USD' in content:
                import re
                chf_usd_match = re.search(r'CHF/USD.*?(\d+\.\d+)', content)
                if chf_usd_match:
                    chf_usd_rate = float(chf_usd_match.group(1))
                    
                    if from_currency == 'CHF' and to_currency == 'USD':
                        return chf_usd_rate
                    elif from_currency == 'USD' and to_currency == 'CHF':
                        return 1 / chf_usd_rate
        
        # Taux par défaut
        if from_currency == 'CHF' and to_currency == 'USD':
            return 1.25
        elif from_currency == 'USD' and to_currency == 'CHF':
            return 0.80
        else:
            return 1.0
            
    except Exception as e:
        logger.error(f"Erreur taux de change: {e}")
        return 1.0
