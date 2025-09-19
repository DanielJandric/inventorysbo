from __future__ import annotations

from typing import Any, Dict

from ..config import AppConfig
from ..services.ai_engine import AIEngine


class MarketsService:
    def __init__(self, cfg: AppConfig, ai: AIEngine):
        self.cfg = cfg
        self.ai = ai

    def handle_message(self, message: str) -> Dict[str, Any]:
        m = (message or "").lower()

        # Quick canned replies for short market questions
        if len(message) < 80:
            if any(k in m for k in ["indices", "bourse", "cac", "dow", "nasdaq"]):
                return {"reply": "Principaux indices (indicatif): S&P500 ~4500, NASDAQ ~14000, CAC40 ~7500, SMI ~11500.", "metadata": {"mode": "ultra_quick_markets"}}
            if any(k in m for k in ["bitcoin", "btc", "crypto", "ethereum"]):
                return {"reply": "Crypto (indicatif): BTC ~$65k, ETH ~$3.5k. Volatilité élevée (DYOR).", "metadata": {"mode": "ultra_quick_crypto"}}
            if any(k in m for k in ["sentiment", "tendance", "bullish", "bearish"]):
                return {"reply": "Sentiment global: neutre à légèrement haussier; VIX modéré ~15–20.", "metadata": {"mode": "ultra_quick_sentiment"}}

        if self.ai.is_available:
            prompt = (
                "Tu es un analyste marchés. Réponds en français, concis, structuré, sans inventer de chiffres.\n"
                f"Question: {message}"
            )
            ans = self.ai.ask(prompt)
            if ans:
                return {"reply": ans, "metadata": {"mode": "ai"}}

        return {"reply": "Moteur IA indisponible pour les marchés. Posez une question plus simple ou configurez OPENAI.", "metadata": {"mode": "fallback"}}

