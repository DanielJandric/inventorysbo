from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import AppConfig
from ..services.ai_engine import AIEngine
from ..services.cache import cache
from ..repositories.items_repo import ItemsRepository
from ..models.collection_item import CollectionItem


class ChatbotService:
    def __init__(self, cfg: AppConfig, ai: AIEngine, repo: ItemsRepository):
        self.cfg = cfg
        self.ai = ai
        self.repo = repo

    def _fetch_items(self) -> List[CollectionItem]:
        items = cache.get("items:list")
        if items is not None:
            return items
        raw = self.repo.list_items()
        items = [CollectionItem.from_dict(x) for x in raw]
        cache.set("items:list", items, ttl=60)
        return items

    @staticmethod
    def _is_available(it: CollectionItem) -> bool:
        st = (it.status or "").strip().lower()
        return st not in ("sold", "vendu", "vendue")

    def _value_of(self, it: CollectionItem) -> float:
        # Handle stocks and regular items
        try:
            if it.category == "Actions" and it.current_price and it.stock_quantity and self._is_available(it):
                return float(it.current_price) * int(it.stock_quantity)
            if it.current_value and self._is_available(it):
                return float(it.current_value)
        except Exception:
            pass
        return 0.0

    def _quick_answer(self, message: str, items: List[CollectionItem]) -> Optional[str]:
        m = (message or "").lower()
        # Count objects
        if "combien" in m and ("objet" in m or "item" in m):
            return f"Vous avez {len(items)} objets dans votre collection."
        # Total value
        if "valeur" in m and ("total" in m or "totale" in m or "combien vaut" in m):
            total = sum(self._value_of(it) for it in items)
            avail = sum(1 for it in items if self._is_available(it))
            return f"Valeur totale estimée: {int(total):,} CHF (disponibles: {avail}).".replace(",", " ")
        # Top items
        if ("top" in m) or ("plus" in m and "cher" in m):
            top = sorted(items, key=self._value_of, reverse=True)[:3]
            lines = [f"{i+1}. {it.name or 'N/A'} ~{int(self._value_of(it)):,} CHF".replace(",", " ") for i, it in enumerate(top)]
            return "Top 3 des objets:\n" + ("\n".join(lines) if lines else "(n/a)")
        return None

    def handle_message(self, message: str, *, session_id: Optional[str] = None) -> Dict[str, Any]:
        items = self._fetch_items()
        # Fast path for short queries unless forced LLM
        if not self.cfg.ALWAYS_LLM and len(message) < 80:
            qa = self._quick_answer(message, items)
            if qa:
                return {"reply": qa, "metadata": {"mode": "ultra_quick"}}

        # Compose a compact context
        cats: dict[str, int] = {}
        for it in items:
            c = (it.category or "Autres").strip()
            cats[c] = cats.get(c, 0) + 1
        top = sorted(items, key=self._value_of, reverse=True)[:5]
        top_lines = [f"- {it.name or '?'} ({it.category or '?'}) ~{int(self._value_of(it)):,} CHF".replace(",", " ") for it in top if self._value_of(it) > 0]
        ctx = "Contexte Collection: catégories=[" + ", ".join([f"{k}:{v}" for k, v in cats.items()]) + "]\n" + ("Top par valeur:\n" + "\n".join(top_lines) if top_lines else "")

        if self.ai.is_available:
            prompt = (
                "Tu es l'assistant BONVIN. Réponds en français, de façon concise et structurée.\n\n"
                + (ctx + "\n\n" if ctx else "")
                + f"Question: {message}"
            )
            out = self.ai.ask(prompt)
            if out:
                return {"reply": out, "metadata": {"mode": "ai"}}

        # Fallback
        return {"reply": "Moteur IA indisponible. Activez OPENAI ou posez une question plus simple.", "metadata": {"mode": "fallback"}}

