#!/usr/bin/env python3
"""
Module d'authentification Yahoo Finance robuste
Utilise les vraies API Yahoo Finance avec gestion automatique des crumbs
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

def get_yahoo_crumb():
    """Obtient un crumb et une session pour l'API Yahoo Finance"""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        logger.info("🔄 Obtention du crumb Yahoo Finance...")
        
        # Première requête pour obtenir les cookies
        response = session.get('https://finance.yahoo.com', headers=headers, timeout=10)
        response.raise_for_status()
        
        # Recherche du crumb dans la réponse avec plusieurs patterns
        crumb_patterns = [
            r'"CrumbStore":{"crumb":"([^"]+)"}',
            r'"crumb":"([^"]+)"',
            r'"CrumbStore":\s*{\s*"crumb":\s*"([^"]+)"',
            r'window\.__INITIAL_STATE__\s*=\s*{[^}]*"crumb":\s*"([^"]+)"',
            r'root\.App\.main\s*=\s*{[^}]*"crumb":\s*"([^"]+)"'
        ]
        
        for pattern in crumb_patterns:
            crumb_match = re.search(pattern, response.text)
            if crumb_match:
                crumb = crumb_match.group(1)
                # Décoder les caractères échappés
                crumb = crumb.replace('\\u002F', '/')
                logger.info(f"✅ Crumb obtenu avec succès: {crumb[:10]}...")
                return session, crumb
        
        # Méthode alternative si le crumb n'est pas trouvé
        logger.warning("⚠️ Crumb non trouvé dans HTML, tentative via API...")
        response = session.get('https://query1.finance.yahoo.com/v1/test/getcrumb', headers=headers, timeout=10)
        if response.status_code == 200:
            crumb = response.text.strip()
            logger.info(f"✅ Crumb obtenu via API: {crumb[:10]}...")
            return session, crumb
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'obtention du crumb: {e}")
    
    return None, None

class YahooFinanceAuth:
    """Gestionnaire d'authentification Yahoo Finance avec vraie API et gestion des crumbs"""
    
    def __init__(self):
        self.session = None
        self.crumb = None
        self.base_url = "https://query1.finance.yahoo.com"
        self.last_request_time = None
        self.min_request_interval = 1.0  # Délai minimum entre les requêtes
        self.max_retries = 3
        self.retry_delay = 2
        self.crumb_lifetime = timedelta(hours=1)
        self.last_crumb_refresh = None
        
        # Headers pour simuler un navigateur réel
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
        
        # Initialiser la session
        self._refresh_crumb()
        logger.info("✅ Module d'authentification Yahoo Finance initialisé avec vraie API")
    
    def _wait_between_requests(self):
        """Attend entre les requêtes pour éviter les rate limits"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed + 0.1
                time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _refresh_crumb(self):
        """Renouvelle le crumb et la session"""
        try:
            self.session, self.crumb = get_yahoo_crumb()
            if not self.crumb:
                raise Exception("Impossible d'obtenir le crumb")
            
            self.last_crumb_refresh = datetime.now()
            logger.info("✅ Crumb renouvelé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du renouvellement du crumb: {e}")
            raise
    
    def _is_crumb_valid(self) -> bool:
        """Vérifie si le crumb actuel est encore valide"""
        if not self.crumb or not self.last_crumb_refresh:
            return False
        
        return datetime.now() - self.last_crumb_refresh < self.crumb_lifetime
    
    def _ensure_valid_crumb(self) -> bool:
        """S'assure qu'un crumb valide est disponible"""
        if not self._is_crumb_valid():
            self._refresh_crumb()
        return True
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Effectue une requête avec gestion des erreurs et retry"""
        if params is None:
            params = {}
        
        self._wait_between_requests()
        
        # S'assurer qu'un crumb valide est disponible
        if not self._ensure_valid_crumb():
            raise Exception("Impossible d'obtenir un crumb valide")
        
        params['crumb'] = self.crumb
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"📡 Requête API: {url} (tentative {attempt + 1})")
                
                response = self.session.get(url, params=params, headers=self.headers, timeout=10)
                
                if response.status_code == 401:  # Crumb expiré
                    logger.warning("⚠️ Crumb expiré, renouvellement...")
                    self._refresh_crumb()
                    params['crumb'] = self.crumb
                    continue
                
                elif response.status_code == 429:  # Rate limit
                    logger.warning(f"⚠️ Rate limit (429), attente... (tentative {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))  # Backoff exponentiel
                        continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Erreur requête (tentative {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Erreur après {self.max_retries} tentatives: {e}")
                time.sleep(self.retry_delay)
        
        raise Exception("Nombre maximum de tentatives atteint")
    
    def get_stock_data(self, symbol: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une action avec gestion automatique des erreurs"""
        try:
            logger.info(f"📊 Récupération données pour {symbol} (tentative {retry_count + 1})")
            
            # Utiliser l'API quote pour les données actuelles
            url = f"{self.base_url}/v6/finance/quote"
            params = {'symbols': symbol}
            
            data = self._make_request(url, params)
            
            if 'quoteResponse' in data and 'result' in data['quoteResponse']:
                results = data['quoteResponse']['result']
                if results:
                    quote = results[0]
                    
                    # Extraire les données essentielles
                    current_price = quote.get('regularMarketPrice')
                    if current_price:
                        return {
                            'symbol': symbol,
                            'price': current_price,
                            'currency': quote.get('currency', 'USD'),
                            'exchange': quote.get('fullExchangeName', ''),
                            'timestamp': datetime.now().isoformat(),
                            'volume': quote.get('regularMarketVolume'),
                            'high': quote.get('regularMarketDayHigh'),
                            'low': quote.get('regularMarketDayLow'),
                            'open': quote.get('regularMarketOpen'),
                            'change': quote.get('regularMarketChange'),
                            'change_percent': quote.get('regularMarketChangePercent'),
                            'market_cap': quote.get('marketCap'),
                            'pe_ratio': quote.get('trailingPE'),
                            'dividend_yield': quote.get('trailingAnnualDividendYield'),
                            'high_52_week': quote.get('fiftyTwoWeekHigh'),
                            'low_52_week': quote.get('fiftyTwoWeekLow'),
                            'previous_close': quote.get('regularMarketPreviousClose')
                        }
            
            logger.warning(f"⚠️ Aucune donnée valide pour {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données pour {symbol}: {e}")
            
            # Gérer les erreurs avec stratégie de récupération
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay * (retry_count + 1))
                return self.get_stock_data(symbol, retry_count + 1)
            
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations détaillées d'une action"""
        try:
            url = f"{self.base_url}/v10/finance/quoteSummary/{symbol}"
            params = {
                'modules': 'assetProfile,summaryProfile,summaryDetail,esgScores,price,financialData,defaultKeyStatistics'
            }
            
            data = self._make_request(url, params)
            
            if 'quoteSummary' in data and 'result' in data['quoteSummary']:
                return data['quoteSummary']['result'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des infos pour {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1d") -> Optional[Dict[str, Any]]:
        """Récupère les données historiques d'une action"""
        try:
            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                'interval': '1d',
                'range': period,
                'includePrePost': 'false',
                'events': 'div,split'
            }
            
            data = self._make_request(url, params)
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                return data['chart']['result'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données historiques pour {symbol}: {e}")
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
                time.sleep(0.5)
                
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