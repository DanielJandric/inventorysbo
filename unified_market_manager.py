#!/usr/bin/env python3
"""
Gestionnaire unifié pour les recherches de cours et mises à jour de marché
Centralise toutes les opérations via les interfaces de recherche web
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from flask import jsonify

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketSource(Enum):
    """Sources de données de marché"""
    OPENAI_WEB_SEARCH = "openai_web_search"
    GOOGLE_SEARCH = "google_search"
    MANUS_API = "manus_api"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"

class MarketUpdateType(Enum):
    """Types de mises à jour de marché"""
    STOCK_PRICE = "stock_price"
    MARKET_BRIEFING = "market_briefing"
    DAILY_NEWS = "daily_news"
    FINANCIAL_MARKETS = "financial_markets"
    MARKET_ALERTS = "market_alerts"

@dataclass
class StockPriceData:
    """Données de prix d'action unifiées"""
    symbol: str
    price: float
    currency: str
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    pe_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    source: str = "unified_market_manager"
    timestamp: str = None
    confidence_score: float = 1.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class MarketUpdateData:
    """Données de mise à jour de marché"""
    update_type: MarketUpdateType
    content: str
    source: MarketSource
    timestamp: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class UnifiedMarketManager:
    """
    Gestionnaire unifié pour toutes les opérations de marché
    Centralise les recherches via les interfaces web search
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'UnifiedMarketManager/1.0'
        })
        
        # Cache pour les données
        self.price_cache = {}
        self.market_cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        logger.info("✅ Gestionnaire de marché unifié initialisé")
    
    def get_stock_price(self, symbol: str, force_refresh: bool = False) -> Optional[StockPriceData]:
        """
        Récupère le prix d'une action via les interfaces web search
        Priorité: OpenAI Web Search -> Google Search -> Manus API
        """
        try:
            # Vérifier le cache si pas de force refresh
            if not force_refresh and symbol in self.price_cache:
                cached_data = self.price_cache[symbol]
                if datetime.fromisoformat(cached_data['timestamp']) + self.cache_duration > datetime.now():
                    logger.info(f"📊 Prix {symbol} récupéré du cache")
                    return StockPriceData(**cached_data)
            
            # Essayer OpenAI Web Search en premier
            price_data = self._get_stock_price_openai_web_search(symbol)
            if price_data:
                self._cache_price_data(symbol, price_data)
                return price_data
            
            # Fallback vers Google Search
            price_data = self._get_stock_price_google_search(symbol)
            if price_data:
                self._cache_price_data(symbol, price_data)
                return price_data
            
            # Fallback vers Manus API
            price_data = self._get_stock_price_manus(symbol)
            if price_data:
                self._cache_price_data(symbol, price_data)
                return price_data
            
            logger.warning(f"⚠️ Aucune source n'a pu fournir le prix pour {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération prix {symbol}: {e}")
            return None
    
    def _get_stock_price_openai_web_search(self, symbol: str) -> Optional[StockPriceData]:
        """Récupère le prix via OpenAI Web Search"""
        try:
            url = f"{self.base_url}/api/web-search/stock/{symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    stock_data = data['data']
                    return StockPriceData(
                        symbol=symbol,
                        price=float(stock_data.get('price', 0)),
                        currency=stock_data.get('currency', 'USD'),
                        change=stock_data.get('change'),
                        change_percent=stock_data.get('change_percent'),
                        volume=stock_data.get('volume'),
                        pe_ratio=stock_data.get('pe_ratio'),
                        fifty_two_week_high=stock_data.get('fifty_two_week_high'),
                        fifty_two_week_low=stock_data.get('fifty_two_week_low'),
                        source="OpenAI Web Search",
                        confidence_score=0.9
                    )
            
            logger.warning(f"⚠️ OpenAI Web Search échoué pour {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur OpenAI Web Search pour {symbol}: {e}")
            return None
    
    def _get_stock_price_google_search(self, symbol: str) -> Optional[StockPriceData]:
        """Récupère le prix via Google Search API"""
        try:
            url = f"{self.base_url}/api/google-search/stock/{symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    stock_data = data['data']
                    return StockPriceData(
                        symbol=symbol,
                        price=float(stock_data.get('price', 0)),
                        currency=stock_data.get('currency', 'USD'),
                        change=stock_data.get('change'),
                        change_percent=stock_data.get('change_percent'),
                        volume=stock_data.get('volume'),
                        pe_ratio=stock_data.get('pe_ratio'),
                        fifty_two_week_high=stock_data.get('fifty_two_week_high'),
                        fifty_two_week_low=stock_data.get('fifty_two_week_low'),
                        source="Google Search API",
                        confidence_score=0.8
                    )
            
            logger.warning(f"⚠️ Google Search API échoué pour {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur Google Search API pour {symbol}: {e}")
            return None
    
    def _get_stock_price_manus(self, symbol: str) -> Optional[StockPriceData]:
        """Récupère le prix via Manus API (fallback)"""
        try:
            # Utiliser l'endpoint existant de Manus
            url = f"{self.base_url}/api/stock-price/{symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    stock_data = data['data']
                    return StockPriceData(
                        symbol=symbol,
                        price=float(stock_data.get('price', 0)),
                        currency=stock_data.get('currency', 'USD'),
                        change=stock_data.get('change'),
                        change_percent=stock_data.get('change_percent'),
                        volume=stock_data.get('volume'),
                        pe_ratio=stock_data.get('pe_ratio'),
                        fifty_two_week_high=stock_data.get('fifty_two_week_high'),
                        fifty_two_week_low=stock_data.get('fifty_two_week_low'),
                        source="Manus API",
                        confidence_score=0.7
                    )
            
            logger.warning(f"⚠️ Manus API échoué pour {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur Manus API pour {symbol}: {e}")
            return None
    
    def get_market_briefing(self, location: str = "global") -> Optional[MarketUpdateData]:
        """
        Récupère un briefing de marché via les interfaces web search
        """
        try:
            # Essayer OpenAI Web Search en premier
            briefing = self._get_market_briefing_openai_web_search()
            if briefing:
                return briefing
            
            # Fallback vers Google Search
            briefing = self._get_market_briefing_google_search(location)
            if briefing:
                return briefing
            
            # Fallback vers Manus API
            briefing = self._get_market_briefing_manus()
            if briefing:
                return briefing
            
            logger.warning("⚠️ Aucune source n'a pu fournir le briefing de marché")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération briefing marché: {e}")
            return None
    
    def _get_market_briefing_openai_web_search(self) -> Optional[MarketUpdateData]:
        """Récupère le briefing via OpenAI Web Search"""
        try:
            url = f"{self.base_url}/api/web-search/market-briefing"
            response = self.session.post(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    return MarketUpdateData(
                        update_type=MarketUpdateType.MARKET_BRIEFING,
                        content=data['data'].get('content', ''),
                        source=MarketSource.OPENAI_WEB_SEARCH,
                        timestamp=datetime.now().isoformat(),
                        metadata={
                            'citations': data['data'].get('citations', []),
                            'confidence_score': 0.9
                        }
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur OpenAI Web Search briefing: {e}")
            return None
    
    def _get_market_briefing_google_search(self, location: str) -> Optional[MarketUpdateData]:
        """Récupère le briefing via Google Search API"""
        try:
            url = f"{self.base_url}/api/google-search/market-report"
            payload = {"location": location}
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    return MarketUpdateData(
                        update_type=MarketUpdateType.MARKET_BRIEFING,
                        content=data['data'].get('content', ''),
                        source=MarketSource.GOOGLE_SEARCH,
                        timestamp=datetime.now().isoformat(),
                        metadata={
                            'location': location,
                            'confidence_score': 0.8
                        }
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur Google Search API briefing: {e}")
            return None
    
    def _get_market_briefing_manus(self) -> Optional[MarketUpdateData]:
        """Récupère le briefing via Manus API"""
        try:
            url = f"{self.base_url}/api/market-report/manus"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    return MarketUpdateData(
                        update_type=MarketUpdateType.MARKET_BRIEFING,
                        content=data['data'].get('content', ''),
                        source=MarketSource.MANUS_API,
                        timestamp=datetime.now().isoformat(),
                        metadata={
                            'confidence_score': 0.7
                        }
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur Manus API briefing: {e}")
            return None
    
    def get_daily_news(self, categories: List[str] = None) -> List[MarketUpdateData]:
        """
        Récupère les nouvelles quotidiennes via Google Search API
        """
        try:
            if categories is None:
                categories = ["finance", "markets", "economy"]
            
            url = f"{self.base_url}/api/google-search/daily-news"
            payload = {"categories": categories}
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    news_items = []
                    for item in data['data'].get('news_items', []):
                        news_items.append(MarketUpdateData(
                            update_type=MarketUpdateType.DAILY_NEWS,
                            content=item.get('content', ''),
                            source=MarketSource.GOOGLE_SEARCH,
                            timestamp=datetime.now().isoformat(),
                            metadata={
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'category': item.get('category', ''),
                                'importance': item.get('importance', 'medium')
                            }
                        ))
                    return news_items
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération nouvelles: {e}")
            return []
    
    def get_market_alerts(self) -> List[MarketUpdateData]:
        """
        Récupère les alertes de marché via OpenAI Web Search
        """
        try:
            url = f"{self.base_url}/api/web-search/market-alerts"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    alerts = []
                    for alert in data['data'].get('alerts', []):
                        alerts.append(MarketUpdateData(
                            update_type=MarketUpdateType.MARKET_ALERTS,
                            content=alert.get('content', ''),
                            source=MarketSource.OPENAI_WEB_SEARCH,
                            timestamp=datetime.now().isoformat(),
                            metadata={
                                'severity': alert.get('severity', 'medium'),
                                'category': alert.get('category', ''),
                                'confidence_score': 0.9
                            }
                        ))
                    return alerts
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération alertes: {e}")
            return []
    
    def update_all_stock_prices(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Met à jour tous les prix d'actions via les interfaces web search
        """
        try:
            if symbols is None:
                # Récupérer les symboles depuis la base de données
                symbols = self._get_all_stock_symbols()
            
            results = {
                'success': True,
                'updated': [],
                'failed': [],
                'total': len(symbols),
                'timestamp': datetime.now().isoformat()
            }
            
            for symbol in symbols:
                try:
                    price_data = self.get_stock_price(symbol, force_refresh=True)
                    if price_data and price_data.price > 0:
                        results['updated'].append({
                            'symbol': symbol,
                            'price': price_data.price,
                            'currency': price_data.currency,
                            'source': price_data.source
                        })
                        logger.info(f"✅ Prix mis à jour pour {symbol}: {price_data.price} {price_data.currency}")
                    else:
                        results['failed'].append({
                            'symbol': symbol,
                            'error': 'Prix non disponible'
                        })
                        logger.warning(f"⚠️ Échec mise à jour prix pour {symbol}")
                except Exception as e:
                    results['failed'].append({
                        'symbol': symbol,
                        'error': str(e)
                    })
                    logger.error(f"❌ Erreur mise à jour {symbol}: {e}")
            
            results['success_count'] = len(results['updated'])
            results['failure_count'] = len(results['failed'])
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour tous les prix: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_all_stock_symbols(self) -> List[str]:
        """Récupère tous les symboles d'actions depuis la base de données"""
        try:
            url = f"{self.base_url}/api/items"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                symbols = []
                for item in data.get('items', []):
                    if item.get('stock_symbol'):
                        symbols.append(item['stock_symbol'])
                return symbols
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération symboles: {e}")
            return []
    
    def _cache_price_data(self, symbol: str, price_data: StockPriceData):
        """Met en cache les données de prix"""
        self.price_cache[symbol] = asdict(price_data)
    
    def clear_cache(self):
        """Vide le cache"""
        self.price_cache.clear()
        self.market_cache.clear()
        logger.info("🗑️ Cache vidé")
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du gestionnaire"""
        return {
            'status': 'operational',
            'cache_size': len(self.price_cache),
            'market_cache_size': len(self.market_cache),
            'base_url': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'sources': [
                'OpenAI Web Search',
                'Google Search API',
                'Manus API'
            ]
        }

def create_unified_market_manager(base_url: str = None) -> UnifiedMarketManager:
    """
    Factory function pour créer une instance du gestionnaire unifié
    """
    if base_url is None:
        base_url = os.getenv('FLASK_BASE_URL', 'http://localhost:5000')
    
    return UnifiedMarketManager(base_url) 