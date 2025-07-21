import requests
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
import json

logger = logging.getLogger(__name__)

class StockPriceData:
    """Données de prix d'action"""
    
    def __init__(self, symbol: str, price: float, currency: str = "USD", 
                 change: float = 0, change_percent: float = 0, volume: int = 0,
                 day_high: float = 0, day_low: float = 0, 
                 fifty_two_week_high: float = 0, fifty_two_week_low: float = 0,
                 exchange: str = "", name: str = "", timestamp: str = "",
                 pe_ratio: float = 0):
        self.symbol = symbol
        self.price = price
        self.currency = currency
        self.change = change
        self.change_percent = change_percent
        self.volume = volume
        self.day_high = day_high
        self.day_low = day_low
        self.fifty_two_week_high = fifty_two_week_high
        self.fifty_two_week_low = fifty_two_week_low
        self.exchange = exchange
        self.name = name
        self.timestamp = timestamp
        self.pe_ratio = pe_ratio
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'symbol': self.symbol,
            'price': self.price,
            'currency': self.currency,
            'change': self.change,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'day_high': self.day_high,
            'day_low': self.day_low,
            'fifty_two_week_high': self.fifty_two_week_high,
            'fifty_two_week_low': self.fifty_two_week_low,
            'exchange': self.exchange,
            'name': self.name,
            'timestamp': self.timestamp,
            'pe_ratio': self.pe_ratio
        }

class ManusStockManager:
    """
    Gestionnaire de cours de bourse utilisant l'API Manus
    """
    
    def __init__(self):
        self.api_base = "https://g8h3ilcvpz3y.manus.space"
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Mapping des régions pour l'API Manus
        self.region_mapping = {
            'US': 'US',
            'SWX': 'CH',  # SIX Swiss Exchange
            'SW': 'CH',   # Suisse
            'LSE': 'GB',  # London Stock Exchange
            'FRA': 'DE',  # Deutsche Börse
            'EPA': 'FR',  # Euronext Paris
            'MIL': 'IT',  # Borsa Italiana
            'AMS': 'NL',  # Euronext Amsterdam
            'VIE': 'AT',  # Wiener Börse
            'STO': 'SE',  # Nasdaq Stockholm
            'OSL': 'NO',  # Oslo Børs
            'CPH': 'DK',  # Nasdaq Copenhagen
            'HEL': 'FI',  # Nasdaq Helsinki
            'ICE': 'IS',  # Nasdaq Iceland
        }
    
    def get_stock_price(self, symbol: str, exchange: Optional[str] = None, 
                       force_refresh: bool = False) -> Optional[StockPriceData]:
        """
        Récupère le prix d'une action via l'API Manus
        """
        try:
            # Formater le symbole
            formatted_symbol = self._format_symbol(symbol, exchange)
            cache_key = f"{formatted_symbol}_{exchange or 'default'}"
            
            # Vérifier le cache
            if not force_refresh and cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.cache_duration):
                    logger.info(f"📊 Cache hit pour {formatted_symbol}")
                    return cached_data['data']
            
            # Déterminer la région
            region = self._get_region(exchange)
            
            # Appel API Manus
            url = f"{self.api_base}/api/custom/stocks"
            params = {
                'symbols': formatted_symbol,
                'region': region
            }
            
            logger.info(f"📊 Appel API Manus pour {formatted_symbol} (région: {region})")
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') and data.get('data'):
                stock_data = data['data'][0]
                
                # Créer l'objet StockPriceData
                price_data = StockPriceData(
                    symbol=stock_data.get('symbol', formatted_symbol),
                    price=stock_data.get('price', 0),
                    currency=stock_data.get('currency', 'USD'),
                    change=stock_data.get('change', 0),
                    change_percent=stock_data.get('change_percent', 0),
                    volume=stock_data.get('volume', 0),
                    day_high=stock_data.get('day_high', 0),
                    day_low=stock_data.get('day_low', 0),
                    fifty_two_week_high=stock_data.get('fifty_two_week_high', 0),
                    fifty_two_week_low=stock_data.get('fifty_two_week_low', 0),
                    exchange=stock_data.get('exchange', exchange or ''),
                    name=stock_data.get('name', ''),
                    timestamp=stock_data.get('timestamp', datetime.now().isoformat()),
                    pe_ratio=stock_data.get('pe_ratio', 0)
                )
                
                # Mettre en cache
                self.cache[cache_key] = {
                    'data': price_data,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"✅ Prix récupéré pour {formatted_symbol}: {price_data.price} {price_data.currency}")
                return price_data
            
            else:
                logger.warning(f"⚠️ Aucune donnée trouvée pour {formatted_symbol}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur API Manus pour {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur inattendue pour {symbol}: {e}")
            return None
    
    def get_multiple_stock_prices(self, symbols: List[str], exchange: Optional[str] = None) -> Dict[str, StockPriceData]:
        """
        Récupère les prix de plusieurs actions en une seule requête
        """
        try:
            # Formater les symboles
            formatted_symbols = [self._format_symbol(symbol, exchange) for symbol in symbols]
            region = self._get_region(exchange)
            
            # Appel API Manus
            url = f"{self.api_base}/api/custom/stocks"
            params = {
                'symbols': ','.join(formatted_symbols),
                'region': region
            }
            
            logger.info(f"📊 Appel API Manus multiple pour {len(symbols)} symboles")
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = {}
            
            if data.get('success') and data.get('data'):
                for stock_data in data['data']:
                    symbol = stock_data.get('symbol', '')
                    
                    price_data = StockPriceData(
                        symbol=symbol,
                        price=stock_data.get('price', 0),
                        currency=stock_data.get('currency', 'USD'),
                        change=stock_data.get('change', 0),
                        change_percent=stock_data.get('change_percent', 0),
                        volume=stock_data.get('volume', 0),
                        day_high=stock_data.get('day_high', 0),
                        day_low=stock_data.get('day_low', 0),
                        fifty_two_week_high=stock_data.get('fifty_two_week_high', 0),
                        fifty_two_week_low=stock_data.get('fifty_two_week_low', 0),
                        exchange=stock_data.get('exchange', exchange or ''),
                        name=stock_data.get('name', ''),
                        timestamp=stock_data.get('timestamp', datetime.now().isoformat()),
                        pe_ratio=stock_data.get('pe_ratio', 0)
                    )
                    
                    results[symbol] = price_data
                    
                    # Mettre en cache individuellement
                    cache_key = f"{symbol}_{exchange or 'default'}"
                    self.cache[cache_key] = {
                        'data': price_data,
                        'timestamp': datetime.now()
                    }
            
            logger.info(f"✅ {len(results)} prix récupérés")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur API Manus multiple: {e}")
            return {}
    
    def _format_symbol(self, symbol: str, exchange: Optional[str] = None) -> str:
        """
        Formate le symbole pour l'API Manus
        """
        # Nettoyer le symbole
        symbol = symbol.strip().upper()
        
        # Gestion des suffixes d'exchange - seulement si pas déjà présent
        if exchange == 'SWX' or exchange == 'SW':
            if not symbol.endswith('.SW') and not symbol.endswith('.SWX'):
                symbol = symbol.replace('.SW', '').replace('.SWX', '') + '.SW'
        elif exchange == 'LSE':
            if not symbol.endswith('.L') and not symbol.endswith('.LSE'):
                symbol = symbol.replace('.L', '').replace('.LSE', '') + '.L'
        elif exchange == 'FRA':
            if not symbol.endswith('.F') and not symbol.endswith('.FRA'):
                symbol = symbol.replace('.F', '').replace('.FRA', '') + '.F'
        
        return symbol
    
    def _get_region(self, exchange: Optional[str] = None) -> str:
        """
        Détermine la région pour l'API Manus
        """
        if exchange:
            return self.region_mapping.get(exchange, 'US')
        return 'US'
    
    def clear_cache(self):
        """
        Vide le cache
        """
        self.cache.clear()
        logger.info("🗑️ Cache vidé")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du cache
        """
        return {
            'cache_size': len(self.cache),
            'cache_duration': self.cache_duration,
            'cached_symbols': list(self.cache.keys())
        }

# Instance globale
manus_stock_manager = ManusStockManager()

def test_manus_stock_manager():
    """
    Test du gestionnaire Manus
    """
    print("🧪 Test du Manus Stock Manager")
    print("=" * 50)
    
    # Test 1: Action US
    print("\n1️⃣ Test AAPL (US):")
    data = manus_stock_manager.get_stock_price('AAPL')
    if data:
        print(f"   Prix: ${data.price:.2f} ({data.change:+.2f}, {data.change_percent:+.2f}%)")
        print(f"   Volume: {data.volume:,}")
        print(f"   Exchange: {data.exchange}")
    else:
        print("   ❌ Échec")
    
    # Test 2: Action suisse
    print("\n2️⃣ Test IREN.SW (Suisse):")
    data = manus_stock_manager.get_stock_price('IREN.SW', exchange='SWX')
    if data:
        print(f"   Prix: {data.price:.2f} {data.currency} ({data.change:+.2f}, {data.change_percent:+.2f}%)")
        print(f"   Volume: {data.volume:,}")
        print(f"   Exchange: {data.exchange}")
    else:
        print("   ❌ Échec")
    
    # Test 3: Multiple
    print("\n3️⃣ Test multiple (AAPL, MSFT, TSLA):")
    results = manus_stock_manager.get_multiple_stock_prices(['AAPL', 'MSFT', 'TSLA'])
    for symbol, data in results.items():
        print(f"   {symbol}: ${data.price:.2f} ({data.change_percent:+.2f}%)")
    
    # Test 4: Cache
    print("\n4️⃣ Test cache:")
    status = manus_stock_manager.get_cache_status()
    print(f"   Taille cache: {status['cache_size']}")
    print(f"   Symboles en cache: {status['cached_symbols']}")
    
    print("\n🎯 Test terminé!")

if __name__ == "__main__":
    test_manus_stock_manager() 