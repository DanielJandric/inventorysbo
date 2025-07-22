#!/usr/bin/env python3
"""
Wrapper de stabilisation pour l'API Manus - Adapté à l'environnement InventorySBO
Architecture de haute disponibilité avec circuit breaker, validation stricte et fallbacks multiples
"""

import time
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import deque, defaultdict
import requests

logger = logging.getLogger(__name__)

class FinancialDataValidator:
    """Validateur strict pour les données financières"""
    
    @staticmethod
    def validate_stock_data(data: Dict[str, Any], symbol: str) -> bool:
        """Valider les données d'une action"""
        try:
            # Vérifications de base
            if not data or not isinstance(data, dict):
                return False
            
            # Vérifier les champs requis
            required_fields = ['symbol', 'price', 'currency']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"⚠️ Champ manquant '{field}' pour {symbol}")
                    return False
            
            # Validation du prix
            price = data.get('price')
            if price is None or price <= 0:
                logger.warning(f"⚠️ Prix invalide pour {symbol}: {price}")
                return False
            
            # Validation du pourcentage de changement
            change_percent = data.get('change_percent', 0)
            if abs(change_percent) > 50:
                logger.warning(f"⚠️ Changement suspect pour {symbol}: {change_percent}%")
                return False
            
            # Validation de la devise
            currency = data.get('currency', 'USD')
            valid_currencies = ['USD', 'CHF', 'EUR', 'GBP']
            if currency not in valid_currencies:
                logger.warning(f"⚠️ Devise invalide pour {symbol}: {currency}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur validation pour {symbol}: {e}")
            return False

class ManusCircuitBreaker:
    """Circuit breaker pour l'API Manus"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Exécuter une fonction avec circuit breaker"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                logger.info("🔄 Circuit breaker: tentative de réouverture")
                self.state = "HALF_OPEN"
            else:
                logger.warning("⚠️ Circuit breaker: circuit ouvert, utilisation du fallback")
                raise Exception("Circuit breaker open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Gestion du succès"""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.info("✅ Circuit breaker: succès, circuit fermé")
    
    def _on_failure(self):
        """Gestion de l'échec"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"🚨 Circuit breaker: {self.failure_count} échecs, circuit ouvert")
        else:
            logger.warning(f"⚠️ Circuit breaker: échec {self.failure_count}/{self.failure_threshold}")

class StabilityMonitor:
    """Monitoring de la stabilité de l'API"""
    
    def __init__(self, window_size: int = 100):
        self.metrics = {
            'success_rate': deque(maxlen=window_size),
            'response_times': deque(maxlen=window_size),
            'error_types': defaultdict(int),
            'total_requests': 0,
            'successful_requests': 0
        }
    
    def record_request(self, success: bool, duration: float, error: Exception = None):
        """Enregistrer une requête"""
        self.metrics['success_rate'].append(1 if success else 0)
        self.metrics['response_times'].append(duration)
        self.metrics['total_requests'] += 1
        
        if success:
            self.metrics['successful_requests'] += 1
        
        if error:
            self.metrics['error_types'][type(error).__name__] += 1
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtenir le statut de santé"""
        if not self.metrics['success_rate']:
            return {
                'healthy': False,
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'total_requests': 0,
                'common_errors': {}
            }
        
        recent_success_rate = sum(self.metrics['success_rate']) / len(self.metrics['success_rate'])
        avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
        
        return {
            'healthy': recent_success_rate > 0.95,
            'success_rate': recent_success_rate,
            'avg_response_time': avg_response_time,
            'total_requests': self.metrics['total_requests'],
            'successful_requests': self.metrics['successful_requests'],
            'common_errors': dict(self.metrics['error_types'])
        }

class StableManusAPI:
    """API Manus stabilisée avec haute disponibilité"""
    
    def __init__(self):
        # Composants de stabilisation
        self.circuit_breaker = ManusCircuitBreaker()
        self.monitor = StabilityMonitor()
        self.validator = FinancialDataValidator()
        
        # Cache local
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes (comme dans manus_integration.py)
        
        # Sources en cascade (utilisant vos modules existants)
        self.primary_source = "manus"
        self.fallback_sources = ["alpha_vantage", "yfinance"]
    
    def get_stock_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Récupérer les données d'une action avec haute disponibilité"""
        start_time = time.time()
        
        try:
            # 1. Vérifier le cache
            if not force_refresh:
                cached_data = self._get_cached_data(symbol)
                if cached_data:
                    self.monitor.record_request(True, time.time() - start_time)
                    return cached_data
            
            # 2. Essayer les sources en cascade
            for source in [self.primary_source] + self.fallback_sources:
                try:
                    data = self._get_data_from_source(symbol, source)
                    if data and self.validator.validate_stock_data(data, symbol):
                        # Mettre en cache et retourner
                        self._cache_data(symbol, data)
                        self.monitor.record_request(True, time.time() - start_time)
                        return data
                except Exception as e:
                    logger.warning(f"⚠️ Source {source} échouée pour {symbol}: {e}")
                    continue
            
            # 3. Retourner les données de cache expirées si disponibles
            stale_data = self._get_cached_data(symbol, ignore_ttl=True)
            if stale_data:
                logger.warning(f"⚠️ Utilisation de données expirées pour {symbol}")
                self.monitor.record_request(True, time.time() - start_time)
                return stale_data
            
            # 4. Données par défaut
            raise Exception("Aucune source disponible")
            
        except Exception as e:
            self.monitor.record_request(False, time.time() - start_time, e)
            logger.error(f"❌ Échec récupération données pour {symbol}: {e}")
            return self._get_default_data(symbol)
    
    def _get_data_from_source(self, symbol: str, source: str) -> Optional[Dict[str, Any]]:
        """Récupérer les données depuis une source spécifique"""
        if source == "manus":
            return self._get_manus_data(symbol)
        elif source == "alpha_vantage":
            return self._get_alpha_vantage_data(symbol)
        elif source == "yfinance":
            return self._get_yfinance_data(symbol)
        else:
            raise ValueError(f"Source inconnue: {source}")
    
    def _get_manus_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupérer les données depuis l'API Manus (avec circuit breaker)"""
        try:
            # Utiliser le circuit breaker avec votre API existante
            return self.circuit_breaker.call(self._call_manus_api, symbol)
        except Exception as e:
            logger.error(f"❌ Erreur API Manus pour {symbol}: {e}")
            return None
    
    def _call_manus_api(self, symbol: str) -> Dict[str, Any]:
        """Appel à votre API Manus existante"""
        from manus_integration import ManusStockAPI
        
        manus_api = ManusStockAPI()
        result = manus_api.get_stock_price(symbol)
        
        if not result or result.get('status') != 'available':
            raise Exception("Manus API returned invalid data")
        
        return result
    
    def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupérer les données depuis Alpha Vantage (votre module existant)"""
        try:
            from alpha_vantage_fallback import alpha_vantage_fallback
            return alpha_vantage_fallback.get_stock_price(symbol)
        except Exception as e:
            logger.error(f"❌ Erreur Alpha Vantage pour {symbol}: {e}")
            return None
    
    def _get_yfinance_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupérer les données depuis yfinance (fallback)"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'price': info.get('currentPrice', 0),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'high_52_week': info.get('fiftyTwoWeekHigh'),
                'low_52_week': info.get('fiftyTwoWeekLow'),
                'open': info.get('regularMarketOpen'),
                'previous_close': info.get('regularMarketPreviousClose'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'NASDAQ'),
                'last_updated': datetime.now().isoformat(),
                'source': 'yfinance',
                'status': 'fallback'
            }
        except Exception as e:
            logger.error(f"❌ Erreur yfinance pour {symbol}: {e}")
            return None
    
    def _get_cached_data(self, symbol: str, ignore_ttl: bool = False) -> Optional[Dict[str, Any]]:
        """Récupérer les données du cache"""
        if symbol not in self.cache:
            return None
        
        cached_data, timestamp = self.cache[symbol]
        
        if ignore_ttl:
            return cached_data
        
        if time.time() - timestamp < self.cache_ttl:
            return cached_data
        
        return None
    
    def _cache_data(self, symbol: str, data: Dict[str, Any]):
        """Mettre en cache les données"""
        self.cache[symbol] = (data, time.time())
    
    def _get_default_data(self, symbol: str) -> Dict[str, Any]:
        """Données par défaut en cas d'échec"""
        return {
            'symbol': symbol,
            'name': symbol,
            'price': 0.0,
            'change': 0.0,
            'change_percent': 0.0,
            'volume': 0,
            'market_cap': None,
            'pe_ratio': None,
            'high_52_week': None,
            'low_52_week': None,
            'open': 0.0,
            'previous_close': 0.0,
            'currency': 'USD',
            'exchange': 'NASDAQ',
            'last_updated': datetime.now().isoformat(),
            'source': 'default',
            'status': 'error',
            'error': 'Aucune source disponible'
        }
    
    def get_multiple_stock_prices(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Récupérer les données de plusieurs actions"""
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_stock_price(symbol, force_refresh)
            except Exception as e:
                logger.error(f"❌ Erreur pour {symbol}: {e}")
                results[symbol] = self._get_default_data(symbol)
        
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtenir le statut de santé complet"""
        return {
            'api_health': self.monitor.get_health_status(),
            'circuit_breaker': {
                'state': self.circuit_breaker.state,
                'failure_count': self.circuit_breaker.failure_count,
                'is_open': self.circuit_breaker.state == "OPEN"
            },
            'cache': {
                'size': len(self.cache),
                'ttl': self.cache_ttl
            },
            'sources': {
                'primary': self.primary_source,
                'fallbacks': self.fallback_sources
            }
        }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Vider le cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"🗑️ Cache vidé ({cache_size} entrées supprimées)")
        return {
            'status': 'success',
            'cleared_entries': cache_size,
            'timestamp': datetime.now().isoformat()
        }

# Instance globale pour compatibilité avec votre code existant
stable_manus_api = StableManusAPI()

# Fonctions de compatibilité avec manus_integration.py
def get_stock_price_stable(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Fonction de compatibilité avec votre API existante"""
    return stable_manus_api.get_stock_price(symbol, force_refresh)

def get_multiple_stock_prices_stable(symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """Fonction de compatibilité pour plusieurs actions"""
    return stable_manus_api.get_multiple_stock_prices(symbols, force_refresh)

def get_health_status_stable() -> Dict[str, Any]:
    """Obtenir le statut de santé"""
    return stable_manus_api.get_health_status() 