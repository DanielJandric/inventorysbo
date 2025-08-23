"""
Routes module for Inventory SBO application.
Contains Flask blueprints for different functionality areas.
"""

from .items import items_bp
from .ai import ai_bp
from .market import market_bp

__version__ = '1.0.0'
__all__ = [
    'items_bp',
    'ai_bp',
    'market_bp'
]