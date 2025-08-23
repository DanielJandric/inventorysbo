"""
Services module for Inventory SBO application.
Contains AI, email, and market services.
"""

from .ai_service import ai_service
from .email_service import email_service
from .market_service import market_service

__version__ = '1.0.0'
__all__ = [
    'ai_service',
    'email_service', 
    'market_service'
]