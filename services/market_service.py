"""
Market and stock services for data retrieval and analysis using yfinance.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from core.app_config import Config
from core.utils import get_live_exchange_rate, retry_on_failure, rate_limit
from core.database import db_manager

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    logger.info("✅ yfinance is available")
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("⚠️ yfinance not available - install with: pip install yfinance")


class MarketService:
    """Centralized market and stock data service using yfinance"""
    
    def __init__(self):
        # Cache for stock prices
        self._stock_cache = {}
        self._cache_duration = 300  # 5 minutes
        
        # Check if yfinance is available
        self.yfinance_available = YFINANCE_AVAILABLE
        
        if not self.yfinance_available:
            logger.warning("⚠️ yfinance not available - stock price functionality limited")
    
    @retry_on_failure(max_retries=3)
    @rate_limit(calls=10, period=60)  # 10 calls per minute
    def get_stock_price(self, symbol: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get stock price using yfinance"""
        if not self.yfinance_available:
            logger.error(f"Cannot get stock price for {symbol} - yfinance not available")
            return None
        
        cache_key = f"stock_{symbol}"
        
        # Check cache if not forcing refresh
        if not force_refresh and cache_key in self._stock_cache:
            cached_data = self._stock_cache[cache_key]
            if (datetime.now() - cached_data['timestamp']).seconds < self._cache_duration:
                return cached_data['data']
        
        try:
            # Create yfinance ticker object
            ticker = yf.Ticker(symbol)
            
            # Get current data
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if hist.empty or len(hist) == 0:
                logger.warning(f"No historical data found for {symbol}")
                return None
            
            # Get the latest price
            latest_price = hist['Close'].iloc[-1]
            
            # Calculate change if we have at least 2 days
            change = None
            change_percent = None
            if len(hist) >= 2:
                prev_price = hist['Close'].iloc[-2]
                change = latest_price - prev_price
                change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
            
            # Get additional info
            volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else None
            currency = info.get('currency', 'USD')
            
            result = {
                'price': float(latest_price),
                'currency': currency,
                'change': float(change) if change is not None else None,
                'change_percent': float(change_percent) if change_percent is not None else None,
                'volume': int(volume) if volume is not None else None,
                'pe_ratio': info.get('trailingPE'),
                'week_52_high': info.get('fiftyTwoWeekHigh'),
                'week_52_low': info.get('fiftyTwoWeekLow'),
                'market_cap': info.get('marketCap'),
                'source': 'yfinance',
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol
            }
            
            # Cache the result
            self._stock_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            logger.info(f"✅ Got stock price for {symbol}: {latest_price} {currency}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get stock price for {symbol}: {e}")
            return None
    
    def update_all_stock_prices(self) -> Dict[str, Any]:
        """Update prices for all stock items in the database"""
        try:
            stock_items = db_manager.get_stock_items()
            
            if not stock_items:
                return {
                    'success': True,
                    'message': 'No stock items found',
                    'updated': 0,
                    'failed': 0
                }
            
            updated_count = 0
            failed_count = 0
            results = []
            
            for item in stock_items:
                symbol = item.get('stock_symbol')
                if not symbol:
                    continue
                
                try:
                    # Get current price
                    price_data = self.get_stock_price(symbol, force_refresh=True)
                    
                    if price_data and price_data.get('price'):
                        # Update item in database
                        success = db_manager.update_stock_price(item['id'], price_data)
                        
                        if success:
                            updated_count += 1
                            results.append({
                                'id': item['id'],
                                'symbol': symbol,
                                'status': 'updated',
                                'price': price_data['price'],
                                'currency': price_data.get('currency', 'USD')
                            })
                        else:
                            failed_count += 1
                            results.append({
                                'id': item['id'],
                                'symbol': symbol,
                                'status': 'db_update_failed'
                            })
                    else:
                        failed_count += 1
                        results.append({
                            'id': item['id'],
                            'symbol': symbol,
                            'status': 'no_price_data'
                        })
                        
                except Exception as e:
                    logger.error(f"Error updating price for {symbol}: {e}")
                    failed_count += 1
                    results.append({
                        'id': item['id'],
                        'symbol': symbol,
                        'status': 'error',
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'updated': updated_count,
                'failed': failed_count,
                'total': len(stock_items),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error updating all stock prices: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_market_briefing(self, briefing_type: str = 'daily') -> Optional[Dict[str, Any]]:
        """Get market briefing using yfinance data"""
        try:
            if not self.yfinance_available:
                return {
                    'summary': 'Market briefing unavailable - yfinance not installed',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get major market indices
            indices = ['^GSPC', '^DJI', '^IXIC', '^FTSE', '^GDAXI', '^FCHI']  # S&P 500, Dow, Nasdaq, FTSE, DAX, CAC
            index_data = []
            
            for symbol in indices:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    
                    if not hist.empty and len(hist) >= 1:
                        latest_price = hist['Close'].iloc[-1]
                        change = None
                        change_percent = None
                        
                        if len(hist) >= 2:
                            prev_price = hist['Close'].iloc[-2]
                            change = latest_price - prev_price
                            change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
                        
                        index_data.append({
                            'symbol': symbol,
                            'name': self._get_index_name(symbol),
                            'price': float(latest_price),
                            'change': float(change) if change is not None else None,
                            'change_percent': float(change_percent) if change_percent is not None else None
                        })
                except Exception as e:
                    logger.warning(f"Failed to get data for {symbol}: {e}")
                    continue
            
            # Create summary
            summary = f"Market briefing for {datetime.now().strftime('%Y-%m-%d')}:\n"
            for idx in index_data:
                direction = "📈" if (idx['change'] or 0) > 0 else "📉" if (idx['change'] or 0) < 0 else "➡️"
                summary += f"{direction} {idx['name']}: {idx['price']:.2f}"
                if idx['change_percent']:
                    summary += f" ({idx['change_percent']:+.2f}%)"
                summary += "\n"
            
            return {
                'summary': summary,
                'indices': index_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'yfinance'
            }
            
        except Exception as e:
            logger.error(f"Error getting market briefing: {e}")
            return {
                'summary': f'Error getting market briefing: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_index_name(self, symbol: str) -> str:
        """Get human-readable name for index symbol"""
        names = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'Nasdaq',
            '^FTSE': 'FTSE 100',
            '^GDAXI': 'DAX',
            '^FCHI': 'CAC 40'
        }
        return names.get(symbol, symbol)
    
    def get_daily_news(self) -> Optional[List[Dict[str, Any]]]:
        """Get daily market news (placeholder - would need news API)"""
        try:
            # This would typically integrate with a news API
            # For now, return a placeholder
            return [
                {
                    'title': 'Market data available via yfinance',
                    'summary': 'Stock prices and market indices are being retrieved from Yahoo Finance',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'system'
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting daily news: {e}")
            return []
    
    def get_exchange_rate(self, from_currency: str, to_currency: str = 'CHF') -> float:
        """Get exchange rate between currencies"""
        try:
            return get_live_exchange_rate(from_currency, to_currency)
        except Exception as e:
            logger.error(f"Error getting exchange rate {from_currency}->{to_currency}: {e}")
            return 1.0
    
    def get_market_alerts(self) -> Optional[List[Dict[str, Any]]]:
        """Get market alerts (placeholder for now)"""
        try:
            # This would typically integrate with news APIs or financial data providers
            # For now, return basic market status
            alerts = []
            
            if self.yfinance_available:
                alerts.append({
                    'type': 'info',
                    'title': 'Market Data Service Active',
                    'message': 'Stock prices are being retrieved from Yahoo Finance',
                    'timestamp': datetime.now().isoformat(),
                    'priority': 'low'
                })
            else:
                alerts.append({
                    'type': 'warning',
                    'title': 'Market Data Service Limited',
                    'message': 'yfinance not available - please install to enable stock price functionality',
                    'timestamp': datetime.now().isoformat(),
                    'priority': 'medium'
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting market alerts: {e}")
            return []
    
    def clear_cache(self):
        """Clear all cached data"""
        self._stock_cache.clear()
        logger.info("Market service cache cleared")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information"""
        return {
            'stock_cache_size': len(self._stock_cache),
            'cache_duration_seconds': self._cache_duration,
            'yfinance_available': self.yfinance_available,
            'service_status': 'active' if self.yfinance_available else 'limited'
        }
    
    def get_stock_history(self, symbol: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """Get stock price history using yfinance"""
        if not self.yfinance_available:
            logger.warning(f"Cannot get stock history for {symbol} - yfinance not available")
            return []
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period=f"{days}d")
            
            if hist.empty:
                logger.warning(f"No historical data found for {symbol}")
                return []
            
            # Convert to list of dictionaries
            history = []
            for date, row in hist.iterrows():
                history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']) if 'Volume' in row else None
                })
            
            logger.info(f"✅ Got {len(history)} days of history for {symbol}")
            return history
            
        except Exception as e:
            logger.error(f"❌ Failed to get stock history for {symbol}: {e}")
            return []


# Create singleton instance
market_service = MarketService()