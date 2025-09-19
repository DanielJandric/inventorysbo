from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

try:
    from supabase import create_client  # type: ignore
except Exception:
    create_client = None  # type: ignore

from ..config import AppConfig


class ItemsRepository:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self._sb = None
        if create_client and cfg.SUPABASE_URL and cfg.SUPABASE_KEY:
            try:
                self._sb = create_client(cfg.SUPABASE_URL, cfg.SUPABASE_KEY)
            except Exception:
                self._sb = None

    @staticmethod
    def from_config(cfg: AppConfig) -> "ItemsRepository":
        return ItemsRepository(cfg)

    def list_items(self) -> List[Dict[str, Any]]:
        # Prefer direct DB for speed if possible
        if self._sb:
            try:
                r = self._sb.table("items").select("*").order("updated_at", desc=True).execute()
                return r.data or []
            except Exception:
                pass
        # Fallback to existing API if configured
        base = (self.cfg.API_BASE_URL or "").strip()
        if base and not (base.startswith("http://") or base.startswith("https://")):
            # Prefer http for localhost-like values
            if base.startswith("127.0.0.1") or base.startswith("localhost"):
                base = "http://" + base
            else:
                base = "https://" + base
        if base:
            try:
                url = base.rstrip("/") + "/api/items"
                r = requests.get(url, timeout=15)
                if r.status_code == 200 and isinstance(r.json(), list):
                    return r.json()
            except Exception:
                pass
        return []

