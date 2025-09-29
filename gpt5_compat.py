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
        import logging
        logger = logging.getLogger(__name__)
        
        # LOG: Type de l'objet réponse
        logger.info(f"🔍 GPT-5 Response Type: {type(res)}")
        logger.info(f"🔍 GPT-5 Response Dir: {[attr for attr in dir(res) if not attr.startswith('_')][:20]}")
        
        # Try direct output_text attribute first
        text = getattr(res, "output_text", None)
        logger.info(f"🔍 Direct output_text: {text[:100] if text else 'None'}")
        if text:
            return str(text)
        
        # Try output array - AGRÉGER TOUS LES messages.output_text (critique!)
        outputs = getattr(res, "output", None) or []
        logger.info(f"🔍 Output array length: {len(outputs) if outputs else 0}")
        
        # LOG: Inspecter le premier item de output
        if outputs and len(outputs) > 0:
            first_item = outputs[0]
            logger.info(f"🔍 output[0] type: {type(first_item)}")
            logger.info(f"🔍 output[0] attributes: {[a for a in dir(first_item) if not a.startswith('_')][:15]}")
            if hasattr(first_item, 'type'):
                logger.info(f"🔍 output[0].type: {first_item.type}")
            if hasattr(first_item, 'model_dump'):
                try:
                    dump = first_item.model_dump()
                    logger.info(f"🔍 output[0] keys: {list(dump.keys())}")
                except:
                    pass
        
        parts: List[str] = []
        message_count = 0
        
        # Parcourir TOUS les items, pas juste le premier
        for idx, item in enumerate(outputs):
            try:
                item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
                logger.info(f"🔍 output[{idx}].type = {item_type}")
                
                if item_type == "message":
                    message_count += 1
                    logger.info(f"🔍 Processing message #{message_count}")
                    
                    content = getattr(item, "content", None) or (item.get("content") if isinstance(item, dict) else [])
                    for c in content or []:
                        c_type = getattr(c, "type", None) or (c.get("type") if isinstance(c, dict) else None)
                        
                        # CRITIQUE: Chercher output_text spécifiquement
                        if c_type == "output_text":
                            t = getattr(c, "text", None) or (c.get("text") if isinstance(c, dict) else "")
                            if t:
                                logger.info(f"  ✅ Found output_text: {len(t)} chars")
                                parts.append(str(t))
                        elif c_type == "text":  # Fallback
                            t = getattr(c, "text", None) or (c.get("text") if isinstance(c, dict) else "")
                            if t:
                                logger.info(f"  ✅ Found text: {len(t)} chars")
                                parts.append(str(t))
            except Exception as e:
                logger.warning(f"Error extracting from output item: {e}")
                continue
        
        logger.info(f"🔍 Total messages processed: {message_count}, parts found: {len(parts)}")
        
        if parts:
            logger.info(f"✅ Extracted {len(parts)} parts via output array")
            return "".join(parts)
        
        logger.warning("⚠️ No parts found in output array, trying dict conversion...")
        
        # GPT-5 peut utiliser un format différent - essayer de convertir en dict et extraire
        try:
            if hasattr(res, 'model_dump'):
                res_dict = res.model_dump()
                logger.info("🔍 Using model_dump()")
            elif hasattr(res, 'to_dict'):
                res_dict = res.to_dict()
                logger.info("🔍 Using to_dict()")
            else:
                res_dict = dict(res) if hasattr(res, '__iter__') else {}
                logger.info("🔍 Using dict() cast")
            
            # LOG: Structure de la réponse
            logger.info(f"🔍 Response dict keys: {list(res_dict.keys())[:20]}")
            
            # LOG: Échantillon des premières clés/valeurs
            for key in list(res_dict.keys())[:5]:
                value = res_dict[key]
                if isinstance(value, str):
                    logger.info(f"🔍   {key}: {value[:100]}")
                else:
                    logger.info(f"🔍   {key}: {type(value)}")
            
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
                logger.info(f"✅ Found text via recursive search: {found_text[:100]}")
                return str(found_text)
            else:
                logger.error("❌ Recursive search found NO text!")
                # LOG: Dump complet pour debug (limité)
                import json
                try:
                    dump = json.dumps(res_dict, indent=2, default=str)[:2000]
                    logger.error(f"📋 Response structure sample:\n{dump}")
                except:
                    logger.error(f"📋 Cannot JSON dump, raw keys: {res_dict.keys()}")
        except Exception as e:
            logger.error(f"Error in fallback extraction: {e}", exc_info=True)
        
        logger.error("❌ ALL extraction methods failed - returning empty string")
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
        # Note: modalities pas encore supporté dans SDK v1.x
    }
    
    # CRITIQUE: instructions au lieu de system dans input
    if instructions_text:
        req["instructions"] = instructions_text
    
    # max_output_tokens en racine (format actuel SDK)
    if max_output_tokens is not None:
        req["max_output_tokens"] = max_output_tokens
    
    # LOG: Requête finale
    logger.info(f"📤 Sending request with keys: {list(req.keys())}")
    
    # Support per-call timeout via client.with_options when provided
    try:
        _client = client.with_options(timeout=timeout) if timeout else client
    except Exception:
        _client = client
    # Some server SDK versions do not accept response_format for Responses API.
    # We intentionally ignore it here and enforce JSON via prompting and robust parsing upstream.
    
    try:
        response = _client.responses.create(**req)
        logger.info(f"📥 Response received: {type(response)}")
        return response
    except Exception as e:
        logger.error(f"❌ API call failed: {e}", exc_info=True)
        raise


def extract_output_text(res: Any) -> str:
    """Public helper to extract output text from a Responses API result."""
    return _extract_output_text_from_response(res)


