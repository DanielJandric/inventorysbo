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
    """Convertit messages au format Responses API.
    
    CRITIQUE: TOUS les messages d'ENTRÉE utilisent input_text (même assistant!)
    output_text est réservé à la SORTIE du modèle uniquement.
    """
    typed: List[Dict[str, Any]] = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            # Garder tel quel si déjà formaté
            typed.append({"role": role, "content": content})
        else:
            # ⭐ TOUS les rôles utilisent input_text pour l'entrée
            typed.append({"role": role, "content": [{"type": "input_text", "text": str(content)}]})
    return typed


def _extract_output_text_from_response(res: Any) -> str:
    """Extraction robuste de texte - gère objets Pydantic et dicts, ignore reasoning/tools."""
    import logging
    logger = logging.getLogger(__name__)

    # Helper pour accès unifié (objet Pydantic OU dict)
    def get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # 0) Helper direct s'il existe (optimal)
    txt = getattr(res, "output_text", None)
    if txt:
        logger.info("✅ output_text helper present")
        return str(txt)

    # 1) Récupérer output sous forme liste (objets Pydantic OU dict)
    outputs = getattr(res, "output", None)
    if outputs is None and hasattr(res, "model_dump"):
        outputs = res.model_dump().get("output", [])
    if outputs is None and isinstance(res, dict):
        outputs = res.get("output", [])
    outputs = outputs or []

    logger.info(f"🔍 outputs len = {len(outputs)}")

    parts = []

    # 2) Parcourir tous les items, ne prendre QUE les 'message'
    for i, item in enumerate(outputs):
        itype = get(item, "type")
        logger.info(f"  • output[{i}].type = {itype}")

        # CRITIQUE: On ne prend QUE les 'message' (ignore reasoning, tool_call, etc.)
        if itype != "message":
            continue

        content = get(item, "content", []) or []
        for j, c in enumerate(content):
            ctype = get(c, "type")
            if ctype == "output_text":
                t = get(c, "text", "")
                if t:
                    logger.info(f"    → message.content[{j}].output_text: {len(t)} chars")
                    parts.append(str(t))

    if parts:
        logger.info(f"✅ Extracted {len(parts)} parts from messages")
        return "".join(parts)

    # 3) Fallback: certains SDK stockent directement 'text' dans content
    logger.warning("⚠️ No output_text found, trying fallback 'text'...")
    for item in outputs:
        if get(item, "type") == "message":
            content = get(item, "content", []) or []
            for c in content:
                t = get(c, "text")
                if isinstance(t, str) and t.strip():
                    logger.info(f"✅ Found via fallback text: {len(t)} chars")
                    return t

    # 4) Rien trouvé => retourne chaîne vide (JAMAIS les instructions!)
    logger.error("❌ No text found in response - returning empty string")
    logger.error("   Note: Si seulement 'reasoning' présent, GPT-5 n'a pas généré de texte")
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
    import logging
    logger = logging.getLogger(__name__)
    
    # Convert messages to Responses API format
    typed_input = _to_responses_input(messages)
    
    # LOG: Inspection avant envoi
    logger.info(f"🔍 Responses API call:")
    logger.info(f"  - Model: {model}")
    logger.info(f"  - Input messages: {len(typed_input)}")
    logger.info(f"  - Max output tokens: {max_output_tokens}")
    logger.info(f"  - Reasoning effort: {reasoning_effort}")
    
    # Log format du premier message
    if typed_input:
        first_msg = typed_input[0]
        logger.info(f"  - First message role: {first_msg.get('role')}")
        logger.info(f"  - First message content type: {type(first_msg.get('content'))}")
        if isinstance(first_msg.get('content'), list) and first_msg['content']:
            logger.info(f"  - First content item: {first_msg['content'][0]}")
    
    # Extraire system pour le mettre en instructions (recommandation OpenAI)
    instructions_text = None
    input_messages = []
    for msg in typed_input:
        if msg.get("role") == "system":
            # Extraire le texte du system message
            content = msg.get("content", [])
            if isinstance(content, list) and content:
                instructions_text = content[0].get("text", "")
        else:
            input_messages.append(msg)
    
    req: Dict[str, Any] = {
        "model": model,
        "input": input_messages if instructions_text else typed_input,
        "reasoning": {"effort": reasoning_effort}
    }
    
    # CRITIQUE: instructions au lieu de system dans input
    if instructions_text:
        req["instructions"] = instructions_text
    
    # max_output_tokens EN RACINE (version SDK actuelle)
    if max_output_tokens is not None:
        req["max_output_tokens"] = max_output_tokens
    
    # LOG: Requête finale avec valeurs
    logger.info(f"📤 Sending request:")
    logger.info(f"   Keys: {list(req.keys())}")
    logger.info(f"   Model: {req.get('model')}")
    logger.info(f"   Input msgs: {len(req.get('input', []))}")
    logger.info(f"   Has instructions: {bool(req.get('instructions'))}")
    logger.info(f"   Max output tokens: {req.get('max_output_tokens')}")
    logger.info(f"   Reasoning effort: {req.get('reasoning', {}).get('effort')}")
    
    # Support per-call timeout via client.with_options when provided
    try:
        _client = client.with_options(timeout=timeout) if timeout else client
    except Exception:
        _client = client
    # Some server SDK versions do not accept response_format for Responses API.
    # We intentionally ignore it here and enforce JSON via prompting and robust parsing upstream.
    
    try:
        # Appel direct (SDK minimaliste)
        response = _client.responses.create(**req)
        logger.info(f"📥 Response received: {type(response)}")
        return response
    except Exception as e:
        logger.error(f"❌ API call failed: {e}", exc_info=True)
        raise


def extract_output_text(res: Any) -> str:
    """Public helper to extract output text from a Responses API result."""
    return _extract_output_text_from_response(res)


