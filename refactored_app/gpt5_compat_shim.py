"""
Lightweight import shim to reuse your existing gpt5_compat helpers if present.
Falls back to minimal stubs when unavailable.
"""
from __future__ import annotations

try:
    # Prefer the project's robust helpers
    from gpt5_compat import from_responses_simple, extract_output_text  # type: ignore
except Exception:  # pragma: no cover
    # Minimal fallbacks
    def from_responses_simple(*, client, model, messages, **kwargs):  # type: ignore
        return client.responses.create(model=model, input=[{"role": m.get("role","user"), "content": [{"type":"input_text", "text": m.get("content","") }]} for m in messages])

    def extract_output_text(res):  # type: ignore
        try:
            return getattr(res, "output_text", "") or ""
        except Exception:
            return ""

