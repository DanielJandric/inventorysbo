#!/usr/bin/env python3
"""
Gestionnaire de prix d'actions avec Yahoo Finance API
Stockage local des prix historiques et gestion intelligente des limites
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import yfinance as yf
import pandas as pd
from yahoo_finance_api import YahooFinanceAPI

# Import du fallback yahooquery
try:
    from yahoo_fallback import YahooQueryFallback
    YAHOOQUERY_AVAILABLE = True
except ImportError:
    YAHOOQUERY_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class StockPriceData:
    """Données de prix d'action"""
    symbol: str
    price: float
    currency: str
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    high_52_week: Optional[float] = None
    low_52_week: Optional[float] = None
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class StockPriceManager:
    """Gestionnaire de prix d'actions avec stockage local et gestion robuste des erreurs"""
    
    def __init__(self, data_dir: str = "stock_data"):
        self.data_dir = data_dir
        self.cache_file = os.path.join(data_dir, "price_cache.json")
        self.history_file = os.path.join(data_dir, "price_history.json")
        self.daily_requests_file = os.path.join(data_dir, "daily_requests.json")
        
        # Créer le répertoire de données s'il n'existe pas
        os.makedirs(data_dir, exist_ok=True)
        
        # Limites de l'API - 10 requêtes par jour maximum
        self.max_daily_requests = 10
        self.cache_duration = 86400  # 24 heures de cache (pas de temps réel)
        
        # Verrou pour éviter les conflits en webapp
        self._lock = threading.Lock()
        self._request_locks = {}  # Verrous par symbole
        
        # Initialiser l'authentification Yahoo Finance
        try:
            self.yahoo_auth = YahooFinanceAPI()
            logger.info("✅ Module d'authentification Yahoo Finance initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Yahoo Finance API: {e}")
            self.yahoo_auth = None
        
        # Initialiser le fallback yahooquery
        self.yahoo_fallback = None
        if YAHOOQUERY_AVAILABLE:
            try:
                self.yahoo_fallback = YahooQueryFallback()
                logger.info("✅ Module de fallback yahooquery initialisé")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation yahooquery fallback: {e}")
        else:
            logger.warning("⚠️ yahooquery non disponible pour le fallback")
        
        # Charger les données existantes
        self._load_cache()
        self._load_history()
        self._load_daily_requests()
    
    def _get_symbol_lock(self, symbol: str) -> threading.Lock:
        """Obtient ou crée un verrou pour un symbole spécifique"""
        if symbol not in self._request_locks:
            self._request_locks[symbol] = threading.Lock()
        return self._request_locks[symbol]
    
    def _load_cache(self):
        """Charge le cache des prix"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.price_cache = json.load(f)
                logger.info(f"Cache chargé: {len(self.price_cache)} entrées")
            else:
                self.price_cache = {}
        except Exception as e:
            logger.error(f"Erreur chargement cache: {e}")
            self.price_cache = {}
    
    def _save_cache(self):
        """Sauvegarde le cache des prix"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {e}")
    
    def _load_history(self):
        """Charge l'historique des prix"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.price_history = json.load(f)
                logger.info(f"Historique chargé: {len(self.price_history)} symboles")
            else:
                self.price_history = {}
        except Exception as e:
            logger.error(f"Erreur chargement historique: {e}")
            self.price_history = {}
    
    def _save_history(self):
        """Sauvegarde l'historique des prix"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde historique: {e}")
    
    def _load_daily_requests(self):
        """Charge le compteur de requêtes quotidiennes"""
        try:
            if os.path.exists(self.daily_requests_file):
                with open(self.daily_requests_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.daily_requests = data.get('requests', 0)
                    self.last_request_date = data.get('date', '')
                
                # Réinitialiser si c'est un nouveau jour
                today = datetime.now().strftime('%Y-%m-%d')
                if self.last_request_date != today:
                    self.daily_requests = 0
                    self.last_request_date = today
                    self._save_daily_requests()
            else:
                self.daily_requests = 0
                self.last_request_date = datetime.now().strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"Erreur chargement requêtes quotidiennes: {e}")
            self.daily_requests = 0
            self.last_request_date = datetime.now().strftime('%Y-%m-%d')
    
    def _save_daily_requests(self):
        """Sauvegarde le compteur de requêtes quotidiennes"""
        try:
            data = {
                'requests': self.daily_requests,
                'date': self.last_request_date
            }
            with open(self.daily_requests_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde requêtes quotidiennes: {e}")
    
    def _can_make_request(self) -> bool:
        """Vérifie si on peut faire une requête API"""
        return self.daily_requests < self.max_daily_requests
    
    def _increment_request_count(self):
        """Incrémente le compteur de requêtes"""
        self.daily_requests += 1
        self._save_daily_requests()
        logger.info(f"Requête API #{self.daily_requests}/{self.max_daily_requests}")
    
    def _format_symbol(self, symbol: str, exchange: Optional[str] = None) -> str:
        """Formate le symbole pour Yahoo Finance"""
        # Nettoyer le symbole
        symbol = symbol.strip().upper()
        
        # Gestion des bourses suisses
        if exchange and exchange.upper() in ['SWX', 'SIX', 'SWISS', 'CH']:
            if not symbol.endswith('.SW'):
                return f"{symbol}.SW"
        
        # Gestion des bourses européennes
        if exchange and exchange.upper() in ['LSE', 'LONDON']:
            if not symbol.endswith('.L'):
                return f"{symbol}.L"
        
        # Gestion des bourses américaines (par défaut)
        if not any(symbol.endswith(suffix) for suffix in ['.SW', '.L', '.TO', '.V', '.AX']):
            return symbol
        
        return symbol
    
    def get_stock_price(self, symbol: str, exchange: Optional[str] = None, force_refresh: bool = False) -> Optional[StockPriceData]:
        """Récupère le prix d'une action avec gestion optimisée des requêtes et verrouillage"""
        formatted_symbol = self._format_symbol(symbol, exchange)
        
        # Utiliser un verrou par symbole pour éviter les conflits
        symbol_lock = self._get_symbol_lock(formatted_symbol)
        
        with symbol_lock:
            return self._get_stock_price_internal(formatted_symbol, force_refresh)
    
    def _get_stock_price_internal(self, formatted_symbol: str, force_refresh: bool = False) -> Optional[StockPriceData]:
        """Méthode interne pour récupérer le prix d'une action"""
        # Vérifier le cache en priorité (pas de temps réel)
        if formatted_symbol in self.price_cache:
            cached_data = self.price_cache[formatted_symbol]
            cache_age = time.time() - cached_data.get('timestamp', 0)
            
            # Utiliser le cache si moins de 24h ou si pas de refresh forcé
            if cache_age < self.cache_duration and not force_refresh:
                logger.info(f"Prix depuis le cache pour {formatted_symbol} (âge: {cache_age/3600:.1f}h)")
                return StockPriceData(**cached_data['data'])
        
        # Vérifier les limites de l'API
        if not self._can_make_request():
            logger.warning(f"Limite quotidienne atteinte ({self.max_daily_requests} requêtes). Utilisation du cache.")
            if formatted_symbol in self.price_cache:
                cached_data = self.price_cache[formatted_symbol]
                return StockPriceData(**cached_data['data'])
            return None
        
        try:
            # Utiliser le nouveau module d'authentification si disponible
            if self.yahoo_auth:
                logger.info(f"Récupération prix pour {formatted_symbol} via Yahoo Finance Auth (requête #{self.daily_requests + 1})")
                
                # Récupérer les données via le module d'authentification
                yahoo_data = self.yahoo_auth.get_stock_data(formatted_symbol)
                
                if yahoo_data:
                    # Créer l'objet de données
                    price_data = StockPriceData(
                        symbol=formatted_symbol,
                        price=float(yahoo_data['price']),
                        currency=yahoo_data['currency'],
                        change=float(yahoo_data.get('change', 0)),
                        change_percent=float(yahoo_data.get('change_percent', 0)),
                        volume=int(yahoo_data.get('volume', 0)),
                        market_cap=yahoo_data.get('market_cap'),
                        pe_ratio=yahoo_data.get('pe_ratio'),
                        dividend_yield=yahoo_data.get('dividend_yield'),
                        high_52_week=yahoo_data.get('high_52_week'),
                        low_52_week=yahoo_data.get('low_52_week'),
                        timestamp=yahoo_data.get('timestamp', datetime.now().isoformat())
                    )
                    
                    # Incrémenter le compteur de requêtes
                    self._increment_request_count()
                    
                    # Sauvegarder dans le cache
                    self.price_cache[formatted_symbol] = {
                        'data': price_data.to_dict(),
                        'timestamp': time.time()
                    }
                    self._save_cache()
                    
                    # Sauvegarder dans l'historique
                    if formatted_symbol not in self.price_history:
                        self.price_history[formatted_symbol] = []
                    
                    self.price_history[formatted_symbol].append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'time': datetime.now().strftime('%H:%M'),
                        'price': float(yahoo_data['price']),
                        'change': float(yahoo_data.get('change', 0)),
                        'change_percent': float(yahoo_data.get('change_percent', 0)),
                        'volume': int(yahoo_data.get('volume', 0))
                    })
                    
                    # Garder seulement les 30 derniers jours
                    if len(self.price_history[formatted_symbol]) > 30:
                        self.price_history[formatted_symbol] = self.price_history[formatted_symbol][-30:]
                    
                    self._save_history()
                    
                    logger.info(f"✅ Données mises à jour pour {formatted_symbol}: {yahoo_data['price']} {yahoo_data['currency']}")
                    return price_data
                else:
                    logger.warning(f"Aucune donnée récupérée pour {formatted_symbol} via Yahoo Finance Auth")
            
            # Fallback vers yahooquery si disponible
            if self.yahoo_fallback:
                logger.info(f"Fallback vers yahooquery pour {formatted_symbol}")
                yahooquery_data = self.yahoo_fallback.get_stock_data(formatted_symbol)
                
                if yahooquery_data:
                    # Créer l'objet de données
                    price_data = StockPriceData(
                        symbol=formatted_symbol,
                        price=float(yahooquery_data['price']),
                        currency=yahooquery_data['currency'],
                        change=float(yahooquery_data.get('change', 0)),
                        change_percent=float(yahooquery_data.get('change_percent', 0)),
                        volume=int(yahooquery_data.get('volume', 0)),
                        market_cap=yahooquery_data.get('market_cap'),
                        pe_ratio=yahooquery_data.get('pe_ratio'),
                        dividend_yield=yahooquery_data.get('dividend_yield'),
                        high_52_week=yahooquery_data.get('high_52_week'),
                        low_52_week=yahooquery_data.get('low_52_week'),
                        timestamp=yahooquery_data.get('timestamp', datetime.now().isoformat())
                    )
                    
                    # Incrémenter le compteur de requêtes
                    self._increment_request_count()
                    
                    # Sauvegarder dans le cache
                    self.price_cache[formatted_symbol] = {
                        'data': price_data.to_dict(),
                        'timestamp': time.time()
                    }
                    self._save_cache()
                    
                    # Sauvegarder dans l'historique
                    if formatted_symbol not in self.price_history:
                        self.price_history[formatted_symbol] = []
                    
                    self.price_history[formatted_symbol].append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'time': datetime.now().strftime('%H:%M'),
                        'price': float(yahooquery_data['price']),
                        'change': float(yahooquery_data.get('change', 0)),
                        'change_percent': float(yahooquery_data.get('change_percent', 0)),
                        'volume': int(yahooquery_data.get('volume', 0))
                    })
                    
                    # Garder seulement les 30 derniers jours
                    if len(self.price_history[formatted_symbol]) > 30:
                        self.price_history[formatted_symbol] = self.price_history[formatted_symbol][-30:]
                    
                    self._save_history()
                    
                    logger.info(f"✅ Données mises à jour via yahooquery pour {formatted_symbol}: {yahooquery_data['price']} {yahooquery_data['currency']}")
                    return price_data
                else:
                    logger.warning(f"Aucune donnée récupérée pour {formatted_symbol} via yahooquery")
            
            # Fallback vers yfinance si yahooquery échoue
            logger.info(f"Fallback vers yfinance pour {formatted_symbol}")
            ticker = yf.Ticker(formatted_symbol)
            
            # Récupérer les informations actuelles avec gestion d'erreur améliorée
            try:
                info = ticker.info
                hist = ticker.history(period="1d")
            except Exception as api_error:
                error_str = str(api_error)
                if "Invalid Crumb" in error_str or "Unauthorized" in error_str:
                    logger.error(f"Erreur d'authentification Yahoo Finance pour {formatted_symbol}: {api_error}")
                    logger.info("Tentative de récupération avec délai...")
                    
                    # Attendre un peu et réessayer
                    time.sleep(2)
                    try:
                        info = ticker.info
                        hist = ticker.history(period="1d")
                    except Exception as retry_error:
                        logger.error(f"Échec de la deuxième tentative pour {formatted_symbol}: {retry_error}")
                        return None
                else:
                    raise api_error
            
            if hist.empty:
                logger.error(f"Aucune donnée trouvée pour {formatted_symbol}")
                return None
            
            # Extraire les données
            current_price = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[0]
            volume = int(hist['Volume'].iloc[-1])
            
            change = current_price - open_price
            change_percent = (change / open_price) * 100 if open_price > 0 else 0
            
            # Récupérer les métriques supplémentaires
            market_cap = info.get('marketCap')
            pe_ratio = info.get('trailingPE')
            dividend_yield = info.get('dividendYield')
            high_52_week = info.get('fiftyTwoWeekHigh')
            low_52_week = info.get('fiftyTwoWeekLow')
            
            # Créer l'objet de données
            price_data = StockPriceData(
                symbol=formatted_symbol,
                price=float(current_price),
                currency=info.get('currency', 'USD'),
                change=float(change),
                change_percent=float(change_percent),
                volume=volume,
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                dividend_yield=dividend_yield,
                high_52_week=high_52_week,
                low_52_week=low_52_week,
                timestamp=datetime.now().isoformat()
            )
            
            # Incrémenter le compteur de requêtes
            self._increment_request_count()
            
            # Sauvegarder dans le cache
            self.price_cache[formatted_symbol] = {
                'data': price_data.to_dict(),
                'timestamp': time.time()
            }
            self._save_cache()
            
            # Sauvegarder dans l'historique
            if formatted_symbol not in self.price_history:
                self.price_history[formatted_symbol] = []
            
            self.price_history[formatted_symbol].append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M'),
                'price': float(current_price),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': volume
            })
            
            # Garder seulement les 30 derniers jours
            if len(self.price_history[formatted_symbol]) > 30:
                self.price_history[formatted_symbol] = self.price_history[formatted_symbol][-30:]
            
            self._save_history()
            
            logger.info(f"✅ Données mises à jour pour {formatted_symbol}: {current_price} {info.get('currency', 'USD')}")
            return price_data
            
        except Exception as e:
            logger.error(f"Erreur récupération prix pour {formatted_symbol}: {e}")
            return None
    
    def get_price_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Récupère l'historique des prix"""
        formatted_symbol = self._format_symbol(symbol)
        
        if formatted_symbol in self.price_history:
            history = self.price_history[formatted_symbol]
            return history[-days:] if days > 0 else history
        
        return []
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retourne le statut du cache et des requêtes"""
        return {
            'cache_size': len(self.price_cache),
            'history_size': len(self.price_history),
            'daily_requests': self.daily_requests,
            'max_daily_requests': self.max_daily_requests,
            'last_request_date': self.last_request_date,
            'can_make_request': self._can_make_request(),
            'cache_duration': self.cache_duration
        }
    
    def clear_cache(self):
        """Vide le cache"""
        with self._lock:
            self.price_cache.clear()
            self._save_cache()
            logger.info("Cache des prix vidé")
    
    def update_all_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """Met à jour tous les prix d'actions avec gestion optimisée"""
        results = {
            'success': [],
            'failed': [],
            'skipped': [],
            'requests_used': 0,
            'cache_used': 0
        }
        
        with self._lock:
            for symbol in symbols:
                try:
                    # Vérifier si on peut faire une requête
                    if not self._can_make_request():
                        logger.warning(f"Limite quotidienne atteinte, arrêt de la mise à jour")
                        results['skipped'].extend(symbols[symbols.index(symbol):])
                        break
                    
                    # Récupérer le prix
                    price_data = self.get_stock_price(symbol, force_refresh=True)
                    
                    if price_data:
                        results['success'].append({
                            'symbol': symbol,
                            'price': price_data.price,
                            'currency': price_data.currency,
                            'change_percent': price_data.change_percent,
                            'volume': price_data.volume
                        })
                        results['requests_used'] += 1
                    else:
                        results['failed'].append(symbol)
                        
                except Exception as e:
                    logger.error(f"Erreur mise à jour {symbol}: {e}")
                    results['failed'].append(symbol)
        
        return results
    
    def reset_daily_requests(self):
        """Réinitialise le compteur de requêtes quotidiennes"""
        with self._lock:
            self.daily_requests = 0
            self.last_request_date = datetime.now().strftime('%Y-%m-%d')
            self._save_daily_requests()
            logger.info("✅ Compteur de requêtes quotidiennes réinitialisé")
            
            return {
                'status': 'success',
                'message': 'Compteur de requêtes réinitialisé',
                'daily_requests': self.daily_requests,
                'last_request_date': self.last_request_date
            }
    
    def get_daily_requests_status(self) -> Dict[str, Any]:
        """Retourne le statut des requêtes quotidiennes"""
        return {
            'daily_requests': self.daily_requests,
            'max_daily_requests': self.max_daily_requests,
            'last_request_date': self.last_request_date,
            'can_make_request': self._can_make_request(),
            'remaining_requests': max(0, self.max_daily_requests - self.daily_requests)
        } 