from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CollectionItem:
    id: Optional[int] = None
    name: str = ""
    category: str = ""
    status: str = "Available"
    current_value: float | None = None
    acquisition_price: float | None = None
    stock_symbol: str | None = None
    stock_quantity: int | None = None
    current_price: float | None = None
    sold_price: float | None = None
    updated_at: str | None = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "CollectionItem":
        return CollectionItem(
            id=d.get("id"),
            name=d.get("name") or "",
            category=d.get("category") or "",
            status=d.get("status") or "Available",
            current_value=_to_float(d.get("current_value")),
            acquisition_price=_to_float(d.get("acquisition_price")),
            stock_symbol=d.get("stock_symbol"),
            stock_quantity=_to_int(d.get("stock_quantity")),
            current_price=_to_float(d.get("current_price")),
            sold_price=_to_float(d.get("sold_price")),
            updated_at=d.get("updated_at"),
        )


def _to_float(v):
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


def _to_int(v):
    try:
        return int(v) if v is not None else None
    except Exception:
        return None

