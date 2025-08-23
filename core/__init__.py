"""
Core module for Inventory SBO application.
Contains configuration, models, database operations, and utilities.
"""

from .app_config import Config
from .models import CollectionItem, QueryIntent, MarketUpdate, ChatMessage, StockPriceInfo, EmailNotification
from .database import db_manager
from .utils import *

__version__ = '1.0.0'
__all__ = [
    'Config',
    'CollectionItem',
    'QueryIntent', 
    'MarketUpdate',
    'ChatMessage',
    'StockPriceInfo',
    'EmailNotification',
    'db_manager'
]