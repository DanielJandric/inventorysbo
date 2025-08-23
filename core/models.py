"""
Data models and dataclasses for the Inventory SBO application.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class CollectionItem:
    """Enhanced data model for a collection item"""
    name: str
    category: str
    status: str
    id: Optional[int] = None
    construction_year: Optional[int] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    current_value: Optional[float] = None
    sold_price: Optional[float] = None
    acquisition_price: Optional[float] = None
    for_sale: bool = False
    sale_status: Optional[str] = None
    sale_progress: Optional[str] = None
    buyer_contact: Optional[str] = None
    intermediary: Optional[str] = None
    current_offer: Optional[float] = None
    commission_rate: Optional[float] = None
    last_action_date: Optional[str] = None
    surface_m2: Optional[float] = None
    rental_income_chf: Optional[float] = None
    location: Optional[str] = None
    # Stock-specific fields
    stock_symbol: Optional[str] = None
    stock_quantity: Optional[int] = None
    stock_purchase_price: Optional[float] = None
    stock_exchange: Optional[str] = None
    stock_currency: Optional[str] = None
    current_price: Optional[float] = None
    last_price_update: Optional[str] = None
    # Additional stock metrics
    stock_volume: Optional[int] = None
    stock_pe_ratio: Optional[float] = None
    stock_52_week_high: Optional[float] = None
    stock_52_week_low: Optional[float] = None
    stock_change: Optional[float] = None
    stock_change_percent: Optional[float] = None
    stock_average_volume: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionItem':
        """Create instance from dictionary"""
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)


class QueryIntent(Enum):
    """Types of sophisticated query intentions"""
    VEHICLE_ANALYSIS = "vehicle_analysis"
    FINANCIAL_ANALYSIS = "financial_analysis"
    SALE_PROGRESS_TRACKING = "sale_progress_tracking"
    MARKET_INTELLIGENCE = "market_intelligence"
    CATEGORY_ANALYTICS = "category_analytics"
    PERFORMANCE_METRICS = "performance_metrics"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    TECHNICAL_SPECS = "technical_specs"
    SEMANTIC_SEARCH = "semantic_search"
    UNKNOWN = "unknown"


@dataclass
class MarketUpdate:
    """Data model for market updates"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    update_type: Optional[str] = None
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class ChatMessage:
    """Data model for chat messages"""
    role: str
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'role': self.role,
            'content': self.content
        }
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        if self.metadata:
            result['metadata'] = self.metadata
        return result


@dataclass
class StockPriceInfo:
    """Data model for stock price information"""
    symbol: str
    price: float
    currency: str
    timestamp: datetime
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class EmailNotification:
    """Data model for email notifications"""
    subject: str
    body: str
    recipients: List[str]
    html_body: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    priority: str = "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)