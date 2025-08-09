from dataclasses import dataclass, field, fields
from typing import List, Optional, Dict, Any
from enum import Enum
import json


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

    @staticmethod
    def get_schema_for_ai() -> Dict[str, str]:
        """Returns a simplified schema of the class for AI prompts."""
        schema = {}
        for f in fields(CollectionItem):
            if f.name != 'embedding':  # Exclude embedding from the schema
                type_name = str(f.type).replace('typing.Optional', '').replace('[', '').replace(']', '').strip()
                schema[f.name] = type_name
        return schema

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        # Use dataclasses.asdict for proper conversion
        from dataclasses import asdict
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionItem':
        """Crée une instance depuis un dictionnaire"""
        # Filtrer seulement les champs valides
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)
