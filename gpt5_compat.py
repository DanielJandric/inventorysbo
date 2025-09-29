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


def _extract_output_text_from_response(res: Any) -> str:
    """Best-effort extraction of text from a Responses API result."""
    try:
        # Try direct output_text attribute first
        text = getattr(res, "output_text", None)
        if text:
            return str(text)
        
        # Try output array
        outputs = getattr(res, "output", None) or []
        parts: List[str] = []
        for item in outputs:
            try:
                item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
                if item_type == "message":
                    content = getattr(item, "content", None) or (item.get("content") if isinstance(item, dict) else [])
                    for c in content or []:
                        c_type = getattr(c, "type", None) or (c.get("type") if isinstance(c, dict) else None)
                        if c_type in ("output_text", "text"):
                            t = getattr(c, "text", None) or (c.get("text") if isinstance(c, dict) else "")
                            if t:
                                parts.append(str(t))
            except Exception as e:
                # Log pour debug
                try:
                    import logging
                    logging.warning(f"Error extracting from output item: {e}")
                except:
                    pass
                continue
        
        if parts:
            return "".join(parts)
        
        # GPT-5 peut utiliser un format différent - essayer de convertir en dict et extraire
        try:
            if hasattr(res, 'model_dump'):
                res_dict = res.model_dump()
            elif hasattr(res, 'to_dict'):
                res_dict = res.to_dict()
            else:
                res_dict = dict(res) if hasattr(res, '__iter__') else {}
            
            # Chercher récursivement du texte dans la structure
            def find_text(obj, depth=0):
                if depth > 5:  # Limite de profondeur
                    return None
                if isinstance(obj, str) and len(obj) > 20:  # Texte significatif (min 20 chars)
                    # Ignorer les IDs de réponse (format: resp_xxxx ou id_xxxx ou juste des hex)
                    if obj.startswith(('resp_', 'id_', 'req_')) or (len(obj) == 64 and all(c in '0123456789abcdef' for c in obj)):
                        return None
                    # Ignorer les timestamps purs
                    if obj.replace('-', '').replace(':', '').replace(' ', '').isdigit():
                        return None
                    return obj
                if isinstance(obj, dict):
                    # IGNORER les clés d'ID explicites
                    skip_keys = {'id', 'response_id', 'request_id', 'session_id', 'model', 'object', 'created', 'usage'}
                    
                    # Chercher dans les clés communes PRIORITAIRES (ordre important)
                    priority_keys = ['text', 'output_text', 'content', 'message', 'response', 'answer', 'reply']
                    for key in priority_keys:
                        if key in obj and key not in skip_keys:
                            result = find_text(obj[key], depth + 1)
                            if result:
                                return result
                    
                    # Chercher dans toutes les autres valeurs (en évitant les IDs)
                    for key, value in obj.items():
                        if key not in skip_keys and key not in priority_keys:
                            result = find_text(value, depth + 1)
                            if result:
                                return result
                if isinstance(obj, list):
                    for item in obj:
                        result = find_text(item, depth + 1)
                        if result:
                            return result
                return None
            
            found_text = find_text(res_dict)
            if found_text:
                return str(found_text)
        except Exception as e:
            try:
                import logging
                logging.warning(f"Error in fallback extraction: {e}")
            except:
                pass
        
        return ""
    except Exception as e:
        try:
            import logging
            logging.error(f"Critical error in _extract_output_text_from_response: {e}")
        except:
            pass
        return ""


def _to_chat_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    chat_msgs: List[Dict[str, str]] = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            # Aggregate typed content parts into one string
            parts: List[str] = []
            for part in content:
                try:
                    text = part.get("text") if isinstance(part, dict) else None
                    if text:
                        parts.append(str(text))
                except Exception:
                    continue
            chat_msgs.append({"role": role, "content": "\n".join(parts)})
        else:
            chat_msgs.append({"role": role, "content": str(content)})
    return chat_msgs


def from_chat_completions_compat(
    *,
    client: OpenAI,
    model: str,
    messages: List[Dict[str, Any]],
    response_format: Optional[Dict[str, Any]] = None,
    max_tokens: Optional[int] = None,
    max_completion_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
    temperature: Optional[float] = None,  # ignored for GPT-5
    tools: Optional[List[Dict[str, Any]]] = None,
):
    """Compatibility wrapper. Force Chat Completions for JSON reliability.

    Returns an object with `.choices[0].message.content` like Chat Completions.
    """
    # Choose a completions-capable model for GPT‑5
    model_cc = model
    if str(model).startswith("gpt-5"):
        model_cc = os.getenv("AI_COMPLETIONS_MODEL", "gpt-5-chat-latest")

    # Chat Completions request (no temperature by policy)
    req_cc: Dict[str, Any] = {
        "model": model_cc,
        "messages": _to_chat_messages(messages),
    }
    if response_format is not None:
        req_cc["response_format"] = response_format
    # Prefer the new max_completion_tokens parameter (required for GPT-5 models)
    # FORCE max_completion_tokens (GPT-5 ne supporte pas max_tokens)
    if max_completion_tokens is not None:
        req_cc["max_completion_tokens"] = max_completion_tokens
    elif max_tokens is not None:
        req_cc["max_completion_tokens"] = max_tokens
    # Ne JAMAIS envoyer max_tokens à GPT-5
    # req_cc.pop("max_tokens", None)  # Supprimé si présent par erreur
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


# --- New: Responses-only helpers ---
def from_responses_simple(
    *,
    client: OpenAI,
    model: str,
    messages: List[Dict[str, Any]],
    max_output_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
    reasoning_effort: str = "medium",
    response_format: Optional[Dict[str, Any]] = None,
):
    """Send messages via Responses API (no tools) and return raw response.

    - Uses typed inputs compatible with Responses API
    - Optionally sets max_output_tokens/timeout/reasoning/response_format
    """
    req: Dict[str, Any] = {
        "model": model,
        "input": _to_responses_input(messages),
        "reasoning": {"effort": reasoning_effort},
    }
    if max_output_tokens is not None:
        req["max_output_tokens"] = max_output_tokens
    # Support per-call timeout via client.with_options when provided
    try:
        _client = client.with_options(timeout=timeout) if timeout else client
    except Exception:
        _client = client
    # Some server SDK versions do not accept response_format for Responses API.
    # We intentionally ignore it here and enforce JSON via prompting and robust parsing upstream.
    return _client.responses.create(**req)


def extract_output_text(res: Any) -> str:
    """Public helper to extract output text from a Responses API result."""
    return _extract_output_text_from_response(res)


