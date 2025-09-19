from __future__ import annotations

import os
from typing import Optional, List, Dict, Any

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from ..config import AppConfig


class AIEngine:
    def __init__(self, client: Optional["OpenAI"], model: Optional[str]):
        self._client = client
        self.model = model

    @property
    def is_available(self) -> bool:
        return self._client is not None and bool(self.model)

    @staticmethod
    def from_config(cfg: AppConfig) -> "AIEngine":
        if OpenAI is None or not cfg.OPENAI_API_KEY:
            return AIEngine(None, None)
        try:
            timeout = int(os.getenv("TIMEOUT_S", "45"))
        except Exception:
            timeout = 45
        client = OpenAI(api_key=cfg.OPENAI_API_KEY, timeout=timeout)
        return AIEngine(client, cfg.AI_MODEL)

    def ask(self, prompt: str) -> Optional[str]:
        if not self.is_available:
            return None
        try:
            from ..gpt5_compat_shim import from_responses_simple, extract_output_text
        except Exception:
            # Fallback: basic chat.completions if compat shim missing
            try:
                res = self._client.chat.completions.create(
                    model=self.model, messages=[{"role": "user", "content": prompt}]
                )
                return (res.choices[0].message.content or "").strip()
            except Exception:
                return None
        try:
            res = from_responses_simple(client=self._client, model=self.model, messages=[{"role": "user", "content": prompt}])
            text = (extract_output_text(res) or "").strip()
            return text or None
        except Exception:
            return None

