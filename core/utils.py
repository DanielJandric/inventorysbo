"""
Utility functions for the Inventory SBO application.
"""

import re
import hashlib
import logging
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from functools import wraps, lru_cache
import time

logger = logging.getLogger(__name__)

# Cache for forex rates
forex_cache = {}
FOREX_CACHE_DURATION = 3600  # 1 hour


def format_currency(value: Optional[float], currency: str = "CHF", decimal_places: int = 2) -> str:
    """Format a value as currency"""
    if value is None:
        return "N/A"
    
    try:
        formatted = f"{value:,.{decimal_places}f}"
        return f"{currency} {formatted}"
    except (ValueError, TypeError):
        return "N/A"


def format_percentage(value: Optional[float], decimal_places: int = 2) -> str:
    """Format a value as percentage"""
    if value is None:
        return "N/A"
    
    try:
        return f"{value:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "N/A"


def format_number(value: Optional[Union[int, float]], use_commas: bool = True) -> str:
    """Format a number with optional comma separators"""
    if value is None:
        return "N/A"
    
    try:
        if use_commas:
            if isinstance(value, int):
                return f"{value:,}"
            else:
                return f"{value:,.2f}"
        else:
            return str(value)
    except (ValueError, TypeError):
        return "N/A"


def to_numeric_or_none(value: Any) -> Optional[float]:
    """Convert a value to numeric or return None"""
    if value is None:
        return None
    
    try:
        # Handle string values
        if isinstance(value, str):
            # Remove common formatting
            value = value.replace(',', '').replace('$', '').replace('€', '').replace('CHF', '').strip()
            if value == '' or value.lower() in ['n/a', 'none', 'null']:
                return None
        
        return float(value)
    except (ValueError, TypeError):
        return None


def clean_date_format(date_str: str) -> Optional[str]:
    """Clean and standardize date format"""
    if not date_str:
        return None
    
    try:
        # Try to parse various date formats
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%dT%H:%M:%S']:
            try:
                dt = datetime.strptime(date_str.split('.')[0], fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        # If it's already ISO format with timezone
        if 'T' in date_str:
            return date_str.split('T')[0]
        
        return date_str
    except Exception:
        return None


def is_item_sold(item: Any) -> bool:
    """Check if an item is sold"""
    if hasattr(item, 'status'):
        return str(item.status).lower() == 'sold'
    elif isinstance(item, dict):
        return str(item.get('status', '')).lower() == 'sold'
    return False


def is_item_available(item: Any) -> bool:
    """Check if an item is available"""
    if hasattr(item, 'status'):
        status = str(item.status).lower()
    elif isinstance(item, dict):
        status = str(item.get('status', '')).lower()
    else:
        return False
    
    return status in ['available', 'disponible', 'active']


def is_item_for_sale(item: Any) -> bool:
    """Check if an item is for sale"""
    if hasattr(item, 'for_sale'):
        return bool(item.for_sale)
    elif isinstance(item, dict):
        return bool(item.get('for_sale', False))
    return False


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry a function on failure with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator


def rate_limit(calls: int = 1, period: float = 1.0):
    """Decorator to rate limit function calls"""
    min_interval = period / calls
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:max_length - len(ext) - 1] + '.' + ext if ext else name[:max_length]
    
    return filename or 'unnamed'


def extract_numbers_from_text(text: str) -> List[float]:
    """Extract all numbers from a text string"""
    if not text:
        return []
    
    # Pattern to match numbers (including decimals and negative)
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    
    return numbers


def calculate_percentage_change(old_value: Optional[float], new_value: Optional[float]) -> Optional[float]:
    """Calculate percentage change between two values"""
    if old_value is None or new_value is None:
        return None
    
    if old_value == 0:
        return 100.0 if new_value > 0 else -100.0 if new_value < 0 else 0.0
    
    return ((new_value - old_value) / abs(old_value)) * 100


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def merge_dicts(dict1: Dict, dict2: Dict, deep: bool = False) -> Dict:
    """Merge two dictionaries"""
    result = dict1.copy()
    
    if not deep:
        result.update(dict2)
    else:
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value, deep=True)
            else:
                result[key] = value
    
    return result


def validate_email(email: str) -> bool:
    """Validate an email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate a URL"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def get_time_ago(timestamp: Union[str, datetime]) -> str:
    """Get human-readable time ago string"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return "Unknown"
    
    now = datetime.now()
    if timestamp.tzinfo:
        from datetime import timezone
        now = datetime.now(timezone.utc)
    
    diff = now - timestamp
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict, parent_key: str = '', separator: str = '_') -> Dict:
    """Flatten a nested dictionary"""
    items = []
    for key, value in d.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


def safe_divide(numerator: Optional[float], denominator: Optional[float], default: float = 0.0) -> float:
    """Safely divide two numbers"""
    if numerator is None or denominator is None or denominator == 0:
        return default
    return numerator / denominator


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


@lru_cache(maxsize=128)
def get_live_exchange_rate(from_currency: str, to_currency: str = 'CHF') -> float:
    """Get live exchange rate with caching"""
    global forex_cache
    
    cache_key = f"{from_currency}_{to_currency}"
    
    # Check cache
    if cache_key in forex_cache:
        cached_data = forex_cache[cache_key]
        if (datetime.now() - cached_data['timestamp']).seconds < FOREX_CACHE_DURATION:
            return cached_data['rate']
    
    # Default to 1.0 if same currency
    if from_currency == to_currency:
        return 1.0
    
    try:
        # Try FreeCurrency API
        from core.config import Config
        api_key = Config.FREECURRENCY_API_KEY
        
        if api_key:
            url = f"https://api.freecurrencyapi.com/v1/latest"
            params = {
                'apikey': api_key,
                'base_currency': from_currency,
                'currencies': to_currency
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and to_currency in data['data']:
                    rate = float(data['data'][to_currency])
                    
                    # Cache the result
                    forex_cache[cache_key] = {
                        'rate': rate,
                        'timestamp': datetime.now()
                    }
                    
                    return rate
    except Exception as e:
        logger.warning(f"Failed to get exchange rate {from_currency}->{to_currency}: {e}")
    
    # Fallback rates
    fallback_rates = {
        'USD_CHF': 0.91,
        'EUR_CHF': 0.98,
        'GBP_CHF': 1.15,
        'JPY_CHF': 0.0061,
        'CHF_USD': 1.10,
        'CHF_EUR': 1.02,
        'CHF_GBP': 0.87,
        'CHF_JPY': 164.0
    }
    
    return fallback_rates.get(cache_key, 1.0)