#!/usr/bin/env python3
"""
Utilitaires pour l'API Responses de GPT-5
Fonctions d'extraction de texte et de gestion des réponses
"""

import json
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text(res) -> str:
    """
    Extraction robuste du texte de la réponse GPT-5
    
    Args:
        res: Objet réponse de l'API Responses
        
    Returns:
        str: Texte extrait ou chaîne vide
    """
    try:
        # 1) Voie rapide - output_text direct
        if getattr(res, "output_text", None):
            t = (res.output_text or "").strip()
            if t:
                logger.debug("✅ Texte extrait via output_text direct")
                return t
        
        # 2) Parcourir la structure "output"
        chunks = []
        for item in getattr(res, "output", []):
            # Messages assistant
            if getattr(item, "role", "") == "assistant":
                for part in getattr(item, "content", []):
                    if getattr(part, "type", "") == "output_text" and getattr(part, "text", None):
                        chunks.append(part.text)
        
        if chunks:
            result = "\n".join(chunks).strip()
            logger.debug("✅ Texte extrait via structure output")
            return result
        
        # 3) Fallback - essayer d'autres attributs
        fallback_attrs = ["text", "content", "response", "message"]
        for attr in fallback_attrs:
            if hasattr(res, attr) and getattr(res, attr):
                value = getattr(res, attr)
                if isinstance(value, str) and value.strip():
                    logger.debug(f"✅ Texte extrait via fallback {attr}")
                    return value.strip()
        
        logger.warning("⚠️ Aucun texte trouvé dans la réponse")
        return ""
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction du texte: {e}")
        return ""

def extract_metadata(res) -> Dict[str, Any]:
    """
    Extraction des métadonnées utiles de la réponse
    
    Args:
        res: Objet réponse de l'API Responses
        
    Returns:
        Dict: Métadonnées extraites
    """
    metadata = {}
    
    try:
        # Request ID
        metadata["request_id"] = getattr(res, "_request_id", None)
        
        # Usage et tokens
        if hasattr(res, "usage") and res.usage:
            usage = res.usage
            metadata["usage"] = {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None)
            }
            
            # Détails des tokens de sortie (si disponibles)
            if hasattr(usage, "output_tokens_details"):
                output_details = usage.output_tokens_details
                metadata["output_tokens_details"] = {
                    "reasoning_tokens": getattr(output_details, "reasoning_tokens", None),
                    "text_tokens": getattr(output_details, "text_tokens", None)
                }
        
        # Status
        metadata["status"] = getattr(res, "status", None)
        
        # Raisonnement (si activé)
        if hasattr(res, "reasoning") and res.reasoning:
            metadata["reasoning"] = {
                "items_count": len(res.reasoning),
                "types": [getattr(item, "type", "unknown") for item in res.reasoning]
            }
        
        # Output structuré (si disponible)
        if hasattr(res, "output") and res.output:
            metadata["output"] = {
                "items_count": len(res.output),
                "types": [getattr(item, "type", "unknown") for item in res.output]
            }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction des métadonnées: {e}")
    
    return metadata

def analyze_response_quality(res) -> Dict[str, Any]:
    """
    Analyse de la qualité de la réponse
    
    Args:
        res: Objet réponse de l'API Responses
        
    Returns:
        Dict: Analyse de la qualité
    """
    analysis = {
        "has_text": False,
        "text_length": 0,
        "reasoning_used": False,
        "potential_issues": []
    }
    
    try:
        # Extraire le texte
        text = extract_text(res)
        analysis["has_text"] = bool(text)
        analysis["text_length"] = len(text)
        
        # Vérifier le raisonnement
        metadata = extract_metadata(res)
        if metadata.get("output_tokens_details", {}).get("reasoning_tokens"):
            analysis["reasoning_used"] = True
            reasoning_tokens = metadata["output_tokens_details"]["reasoning_tokens"]
            
            # Détecter les "drains" de raisonnement
            if reasoning_tokens > 0 and not text.strip():
                analysis["potential_issues"].append(
                    "DRAIN_DE_RAISONNEMENT: Le modèle a consommé des tokens de raisonnement sans émettre de texte"
                )
        
        # Vérifier la longueur du texte
        if text and len(text) < 10:
            analysis["potential_issues"].append("TEXTE_TROP_COURT: La réponse semble incomplète")
        
        # Vérifier le statut
        if metadata.get("status") != "completed":
            analysis["potential_issues"].append(f"STATUS_INCOMPLET: {metadata.get('status')}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse de la qualité: {e}")
        analysis["potential_issues"].append(f"ERREUR_ANALYSE: {e}")
    
    return analysis

def create_responses_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Création d'un client OpenAI configuré pour l'API Responses
    
    Args:
        api_key: Clé API OpenAI (optionnelle, utilise OPENAI_API_KEY par défaut)
        
    Returns:
        OpenAI: Client configuré
    """
    if not api_key:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("Clé API OpenAI requise")
    
    return OpenAI(api_key=api_key)

def create_optimized_prompt(base_instructions: str, force_output: bool = True) -> str:
    """
    Création d'un prompt optimisé pour éviter les drains de raisonnement
    
    Args:
        base_instructions: Instructions de base
        force_output: Forcer la sortie de texte
        
    Returns:
        str: Prompt optimisé
    """
    if force_output:
        output_instructions = """
IMPORTANT: Tu DOIS émettre une réponse finale en texte.
- Commence ta réponse par "OK –"
- Sois concis et direct
- Évite de rester dans le raisonnement interne
"""
        return f"{base_instructions}\n\n{output_instructions}"
    
    return base_instructions

def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Parsing sécurisé d'une réponse JSON
    
    Args:
        text: Texte de la réponse
        
    Returns:
        Dict ou None si parsing échoue
    """
    try:
        # Nettoyer le texte
        cleaned_text = text.strip()
        
        # Essayer de trouver du JSON dans le texte
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # Parser le JSON
        return json.loads(cleaned_text)
        
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ Échec du parsing JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur lors du parsing JSON: {e}")
        return None

def stream_response_text(client: OpenAI, **kwargs) -> str:
    """
    Streaming de la réponse avec accumulation du texte
    
    Args:
        client: Client OpenAI
        **kwargs: Paramètres pour client.responses.stream
        
    Returns:
        str: Texte complet de la réponse
    """
    try:
        with client.responses.stream(**kwargs) as stream:
            buffer = []
            
            for event in stream:
                if event.type == "response.output_text.delta":
                    delta = getattr(event, 'delta', '')
                    buffer.append(delta)
                elif event.type == "response.completed":
                    break
            
            return "".join(buffer).strip()
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du streaming: {e}")
        return ""

# Fonction de compatibilité pour l'ancien code
def extract_output_text(res) -> str:
    """
    Alias pour extract_text (compatibilité)
    """
    return extract_text(res)

# Exemple d'utilisation
if __name__ == "__main__":
    print("🛠️ Module utilitaire GPT-5 Responses")
    print("Fonctions disponibles:")
    print("  - extract_text(res): Extraction robuste du texte")
    print("  - extract_metadata(res): Extraction des métadonnées")
    print("  - analyze_response_quality(res): Analyse de la qualité")
    print("  - create_optimized_prompt(): Création de prompts optimisés")
    print("  - parse_json_response(text): Parsing JSON sécurisé")
    print("  - stream_response_text(): Streaming avec accumulation")
