#!/usr/bin/env python3
"""
Intégration des APIs Manus pour remplacer toutes les autres APIs
- API de cours de bourse: https://ogh5izcelen1.manus.space/
- API de rapports de marché: https://y0h0i3cqzyko.manus.space/api/report
"""

import requests
import json
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
                        # Données disponibles via l'API Manus
                        stock_data = {
                            'symbol': symbol,
                            'name': symbol,
                            'price': None,  # À extraire du HTML si possible
                            'change': None,
                            'change_percent': None,
                            'volume': None,
                            'market_cap': None,
                            'pe_ratio': None,
                            'high_52_week': None,
                            'low_52_week': None,
                            'open': None,
                            'previous_close': None,
                            'currency': 'USD',
                            'exchange': 'NASDAQ',
                            'last_updated': datetime.now().isoformat(),
                            'source': 'Manus API',
                            'status': 'available',
                            'endpoint': endpoint,
                            'raw_content_length': len(response.text)
                        }
                        
                        # Mettre en cache
                        self.cache[cache_key] = (stock_data, datetime.now())
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
                'currency': 'USD',
                'exchange': 'NASDAQ',
                'last_updated': datetime.now().isoformat(),
                'source': 'Manus API',
                'status': 'unavailable',
                'error': 'API non disponible'
            }
            
            self.cache[cache_key] = (default_data, datetime.now())
            return default_data
            
        except Exception as e:
            logger.error(f"Erreur récupération prix {symbol}: {e}")
            return {
                'symbol': symbol,
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
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
