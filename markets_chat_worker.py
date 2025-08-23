from __future__ import annotations

import os
from typing import Generator, Optional

try:
    from openai import OpenAI
except Exception as _e:  # pragma: no cover
    raise RuntimeError("openai SDK is required: pip install -U openai") from _e

from gpt5_compat import extract_output_text, from_responses_simple


class MarketsChatWorker:
    """Minimal, dependency-light chat worker for Markets page.

    - No web search, no DB, no memory
    - Pure OpenAI call with clear system prompt
    - Optional streaming
    """

    def __init__(self, *, api_key: Optional[str] = None, timeout_s: int = 45):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        # Timeout via client options (some SDKs accept keyword)
        try:
            self.client = OpenAI(api_key=api_key, timeout=timeout_s)
        except TypeError:
            # Fallback if 'timeout' not supported in constructor
            self.client = OpenAI(api_key=api_key)
            try:
                self.client = self.client.with_options(timeout=timeout_s)
            except Exception:
                pass

        # Enforce GPT-5 only (ignore non GPT-5 env values)
        env_model = (os.getenv("AI_MODEL") or "gpt-5").strip()
        self.model = env_model if env_model.startswith("gpt-5") else "gpt-5"
        self.max_output_tokens = min(1200, int(os.getenv("MAX_OUTPUT_TOKENS", "1200")))

        # Stable, concise system prompt (verbosity low)
        self.system_prompt = (
            "Tu es un analyste marchés. Réponds en français, concis (verbosité faible), structuré, actionnable. "
            "Ne fournis pas de chiffres non étayés. Utilise **gras** pour les points clés. "
            "Structure 3–5 points puis une conclusion brève."
        )

    def _build_user_input(self, message: str, context: Optional[str]) -> str:
        message = (message or "").strip()
        ctx = (context or "").strip()
        if ctx:
            return f"Contexte:\n{ctx}\n---\nQuestion: {message}"
        return message

    def generate_reply(self, message: str, context: Optional[str] = None) -> str:
        """Synchronous, one-shot reply via Responses API only (no fallback).

        Returns plain text. If model output is empty, returns a safe message instead.
        """
        msg = (message or "").strip()
        if not msg:
            raise ValueError("Message vide")

        user_input = self._build_user_input(msg, context)

        # Responses API (exclusive) – try direct input first
        try:
            res = self.client.responses.create(
                model=self.model,
                instructions=self.system_prompt,
                input=user_input,
                reasoning={"effort": "high"},
                max_output_tokens=self.max_output_tokens,
                store=False,
            )
            text = (extract_output_text(res) or "").strip()
        except Exception:
            text = ""

        # If empty, retry using typed messages via Responses API
        if not text:
            try:
                res2 = from_responses_simple(
                    client=self.client,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_input},
                    ],
                    reasoning_effort="high",
                    max_output_tokens=self.max_output_tokens,
                )
                text = (extract_output_text(res2) or "").strip()
            except Exception:
                text = ""

        return text  # laisser l'endpoint décider si vide => 502

    def stream_reply(self, message: str, context: Optional[str] = None) -> Generator[str, None, None]:
        """Yield response chunks (plain text). No END footer here; caller may add it.
        Best-effort: in case of error, yields an [ERROR:...] footer to the stream.
        """
        msg = (message or "").strip()
        if not msg:
            yield "[ERROR:Message vide]"
            return

        user_input = self._build_user_input(msg, context)
        kwargs = {
            "model": self.model,
            "instructions": self.system_prompt,
            "input": user_input,
            "stream": True,
            "store": False,
        }
        try:
            try:
                streamer = self.client.responses.stream(**kwargs)
                with streamer as stream:
                    for event in stream:
                        etype = getattr(event, "type", None)
                        if etype == "response.output_text.delta":
                            chunk = getattr(event, "delta", None)
                            if chunk:
                                yield str(chunk)
                        elif etype == "error":
                            err = str(getattr(event, "error", "unknown"))
                            yield f"\n\n[ERROR:{err}]"
            except Exception:
                # Non-stream fallback: send whole response at once
                text = self.generate_reply(message=msg, context=context)
                yield text
        except Exception as e:
            yield f"\n\n[ERROR:{e}]"


_singleton: Optional[MarketsChatWorker] = None


def get_markets_chat_worker() -> MarketsChatWorker:
    global _singleton
    if _singleton is None:
        _singleton = MarketsChatWorker()
    return _singleton


