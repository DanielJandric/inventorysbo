"""
Modèles de données pour l'application Inventory SBO
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


@dataclass
class CollectionItem:
    """Modèle de données enrichi pour un objet de collection"""
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
    # Champs spécifiques aux actions
    stock_symbol: Optional[str] = None
    stock_quantity: Optional[int] = None
    stock_purchase_price: Optional[float] = None
    stock_exchange: Optional[str] = None
    stock_currency: Optional[str] = None
    current_price: Optional[float] = None
    last_price_update: Optional[str] = None
    # Métriques boursières supplémentaires
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
        """Convertit en dictionnaire"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionItem':
        """Crée une instance depuis un dictionnaire"""
        # Filtrer seulement les champs valides
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)


class QueryIntent(Enum):
    """Types d'intentions sophistiquées"""
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
