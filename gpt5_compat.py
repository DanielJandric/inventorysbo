from __future__ import annotations

import os
import json
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except Exception as _e:  # pragma: no cover
    raise RuntimeError("openai SDK is required: pip install -U openai") from _e


def _to_responses_input(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    typed: List[Dict[str, Any]] = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            # Convert assistant input_text parts to output_text
            if role == "assistant":
                fixed = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "input_text":
                        fixed.append({"type": "output_text", "text": part.get("text", "")})
                    else:
                        fixed.append(part)
                typed.append({"role": role, "content": fixed})
            else:
                typed.append({"role": role, "content": content})
        else:
            part_type = "output_text" if role == "assistant" else "input_text"
            typed.append({"role": role, "content": [{"type": part_type, "text": str(content)}]})
    return typed


def from_chat_completions_compat(
    *,
    client: OpenAI,
    model: str,
    messages: List[Dict[str, Any]],
    response_format: Optional[Dict[str, Any]] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
    temperature: Optional[float] = None,  # ignored for GPT-5
    tools: Optional[List[Dict[str, Any]]] = None,
):
    """Compatibility wrapper. For GPT‑5, use Responses API; for GPT‑4.*, defer to Chat Completions.

    Returns an object with `.choices[0].message.content` to mimic Chat Completions.
    """
    if str(model).startswith("gpt-5"):
        req: Dict[str, Any] = {
            "model": model,
            "input": _to_responses_input(messages),
        }
        if tools:
            req["tools"] = tools
        effort = os.getenv("AI_REASONING_EFFORT", "medium")
        req["reasoning"] = {"effort": effort}
        # Do not pass response_format for GPT-5 Responses API in this SDK version
        if max_tokens is not None:
            req["max_output_tokens"] = max_tokens
        # Do not send temperature for GPT-5 to keep determinism and avoid 400
        if timeout is not None:
            req["timeout"] = timeout
        res = client.responses.create(**req)
        text = getattr(res, "output_text", "") or ""

        # Build a minimal Chat Completions-like response structure
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
            _raw=res,
        )

    # Legacy path: chat.completions (no temperature to honor global policy)
    req_cc: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if response_format is not None:
        req_cc["response_format"] = response_format
    if max_tokens is not None:
        req_cc["max_tokens"] = max_tokens
    if timeout is not None:
        req_cc["timeout"] = timeout
    return client.chat.completions.create(**req_cc)


def chat_tools_messages(
    *,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    model: str,
    client: OpenAI,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: str = "medium",
    verbosity: Optional[str] = None,  # ignored
):
    """Single-turn tool call using Responses API; returns the raw Responses object.

    The caller can inspect `res.output` for `tool_call` items and handle follow-ups
    with `previous_response_id` outside this function.
    """
    req: Dict[str, Any] = {
        "model": model,
        "input": _to_responses_input(messages),
        "tools": tools or [],
        "reasoning": {"effort": reasoning_effort},
    }
    if max_output_tokens is not None:
        req["max_output_tokens"] = max_output_tokens
    # Do NOT include temperature/verbosity
    return client.responses.create(**req)


