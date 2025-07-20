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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
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
        
        # Recherche du crumb dans la réponse
        crumb_match = re.search(r'"CrumbStore":{"crumb":"([^"]+)"}', response.text)
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

class YahooFinanceAPI:
    """Classe pour interagir avec l'API Yahoo Finance"""
    
    def __init__(self):
        self.session = None
        self.crumb = None
        self.base_url = "https://query1.finance.yahoo.com"
        self.last_request_time = None
        self.min_request_interval = 1.0
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
        logger.info("✅ YahooFinanceAPI initialisé avec succès")
    
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
    
    def get_quote(self, symbol: str) -> Dict:
        """Obtient les données actuelles pour un symbole"""
        url = f"{self.base_url}/v8/finance/chart/{symbol}"
        params = {
            'interval': '1d',
            'range': '1d',
            'includePrePost': 'false',
            'events': 'div,split'
        }
        
        data = self._make_request(url, params)
        
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            
            # Extraire les informations nécessaires
            meta = result.get('meta', {})
            timestamp = result.get('timestamp', [])
            indicators = result.get('indicators', {})
            quote = indicators.get('quote', [{}])[0] if indicators.get('quote') else {}
            
            if timestamp and quote.get('close'):
                close_prices = quote['close']
                current_price = close_prices[-1] if close_prices else None
                
                if current_price:
                    return {
                        'regularMarketPrice': current_price,
                        'currency': meta.get('currency', 'USD'),
                        'fullExchangeName': meta.get('exchangeName', ''),
                        'regularMarketVolume': quote.get('volume', [None])[-1] if quote.get('volume') else None,
                        'regularMarketDayHigh': quote.get('high', [None])[-1] if quote.get('high') else None,
                        'regularMarketDayLow': quote.get('low', [None])[-1] if quote.get('low') else None,
                        'regularMarketOpen': quote.get('open', [None])[-1] if quote.get('open') else None,
                        'regularMarketChange': current_price - (quote.get('open', [current_price])[-1] if quote.get('open') else current_price),
                        'regularMarketChangePercent': ((current_price - (quote.get('open', [current_price])[-1] if quote.get('open') else current_price)) / (quote.get('open', [current_price])[-1] if quote.get('open') else current_price)) * 100 if quote.get('open') else 0,
                        'marketCap': meta.get('marketCap'),
                        'trailingPE': meta.get('trailingPE'),
                        'trailingAnnualDividendYield': meta.get('trailingAnnualDividendYield'),
                        'fiftyTwoWeekHigh': meta.get('fiftyTwoWeekHigh'),
                        'fiftyTwoWeekLow': meta.get('fiftyTwoWeekLow'),
                        'regularMarketPreviousClose': meta.get('previousClose')
                    }
        
        return {}
    
    def get_historical_data(self, symbol: str, period1: int, period2: int, 
                          interval: str = '1d') -> Dict:
        """
        Obtient les données historiques
        
        Args:
            symbol: Symbole boursier
            period1: Timestamp Unix de début
            period2: Timestamp Unix de fin
            interval: Intervalle (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)
        """
        url = f"{self.base_url}/v8/finance/chart/{symbol}"
        params = {
            'period1': period1,
            'period2': period2,
            'interval': interval,
            'includePrePost': 'true',
            'events': 'div|split|earn'
        }
        
        return self._make_request(url, params)
    
    def get_historical_data_daterange(self, symbol: str, start_date: datetime, 
                                    end_date: datetime, interval: str = '1d') -> Dict:
        """Version simplifiée avec dates datetime"""
        period1 = int(start_date.timestamp())
        period2 = int(end_date.timestamp())
        return self.get_historical_data(symbol, period1, period2, interval)
    
    def get_options(self, symbol: str, date: Optional[int] = None) -> Dict:
        """Obtient les données d'options"""
        url = f"{self.base_url}/v7/finance/options/{symbol}"
        params = {}
        if date:
            params['date'] = date
        
        return self._make_request(url, params)
    
    def get_financials(self, symbol: str) -> Dict:
        """Obtient les données financières"""
        url = f"{self.base_url}/v10/finance/quoteSummary/{symbol}"
        params = {
            'modules': 'incomeStatementHistory,balanceSheetHistory,cashflowStatementHistory,financialData'
        }
        
        return self._make_request(url, params)
    
    def get_info(self, symbol: str) -> Dict:
        """Obtient les informations détaillées sur une entreprise"""
        url = f"{self.base_url}/v10/finance/quoteSummary/{symbol}"
        params = {
            'modules': 'assetProfile,summaryProfile,summaryDetail,esgScores,price,financialData,defaultKeyStatistics'
        }
        
        return self._make_request(url, params)
    
    def search_symbols(self, query: str, count: int = 10) -> List[Dict]:
        """Recherche des symboles"""
        url = f"{self.base_url}/v1/finance/search"
        params = {
            'q': query,
            'count': count,
            'newsCount': 0
        }
        
        data = self._make_request(url, params)
        return data.get('quotes', [])
    
    def get_trending_symbols(self, region: str = 'US', count: int = 10) -> List[str]:
        """Obtient les symboles tendance"""
        url = f"{self.base_url}/v1/finance/trending/{region}"
        params = {'count': count}
        
        data = self._make_request(url, params)
        
        symbols = []
        if 'finance' in data and 'result' in data['finance']:
            for result in data['finance']['result']:
                if 'quotes' in result:
                    symbols.extend([q['symbol'] for q in result['quotes']])
        
        return symbols[:count]
    
    def get_market_summary(self) -> List[Dict]:
        """Obtient un résumé des marchés"""
        url = f"{self.base_url}/v6/finance/quote/marketSummary"
        
        data = self._make_request(url)
        
        if 'marketSummaryResponse' in data and 'result' in data['marketSummaryResponse']:
            return data['marketSummaryResponse']['result']
        return []
    
    # Méthodes compatibles avec notre système existant
    def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une action (compatible avec notre système)"""
        try:
            quote = self.get_quote(symbol)
            if quote and 'regularMarketPrice' in quote:
                return {
                    'symbol': symbol,
                    'price': quote['regularMarketPrice'],
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
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données pour {symbol}: {e}")
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

# Fonction utilitaire pour obtenir une instance
def get_yahoo_auth() -> YahooFinanceAPI:
    """Retourne une instance d'authentification Yahoo Finance"""
    return YahooFinanceAPI()

if __name__ == "__main__":
    # Test du module
    logging.basicConfig(level=logging.INFO)
    
    # Initialisation de l'API
    api = YahooFinanceAPI()
    
    # Test de connexion
    if api.test_connection():
        print("✅ YahooFinanceAPI opérationnel")
        
        # Obtenir les données actuelles d'Apple
        quote = api.get_quote("AAPL")
        if quote:
            print(f"Apple - Prix: ${quote.get('regularMarketPrice', 'N/A')}")
            print(f"Variation: {quote.get('regularMarketChangePercent', 'N/A'):.2f}%")
        
        # Obtenir les données historiques sur 30 jours
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        historical = api.get_historical_data_daterange("AAPL", start_date, end_date)
        if 'chart' in historical and 'result' in historical['chart']:
            result = historical['chart']['result'][0]
            if 'indicators' in result and 'quote' in result['indicators']:
                closes = result['indicators']['quote'][0]['close']
                print(f"\nDonnées historiques - {len(closes)} points")
    else:
        print("❌ YahooFinanceAPI non opérationnel") 