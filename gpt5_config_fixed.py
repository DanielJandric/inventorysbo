#!/usr/bin/env python3
"""
Configuration pour la solution GPT-5 FIXÉE
Utilise Chat Completions au lieu de l'API Responses défaillante
"""

import os

# Configuration des modèles Chat Completions qui fonctionnent
AI_COMPLETIONS_MODEL = os.getenv("AI_COMPLETIONS_MODEL", "gpt-5-chat-latest")
AI_MODEL_FALLBACK = os.getenv("AI_MODEL_FALLBACK", "gpt-4o")

# Configuration des tokens et timeouts
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))
TIMEOUT_S = int(os.getenv("TIMEOUT_S", "60"))

# Désactiver l'ancien fallback (plus nécessaire)
FALLBACK_CHAT = os.getenv("FALLBACK_CHAT", "0") == "1"

# Configuration des prompts
DEFAULT_SYSTEM_PROMPT = (
    "Tu es un analyste marchés expert utilisant GPT-5. "
    "MISSION CRITIQUE : tu DOIS analyser le contexte et émettre une réponse finale en français. "
    "RÈGLE ABSOLUE : "
    "1) ANALYSE d'abord le contexte et la question "
    "2) RAISONNE explicitement sur les données disponibles "
    "3) ÉCRIS ta réponse structurée "
)

FORMATTING_RULES = (
    "Réponds de manière concise, actionnable et contextuelle. "
    "Structure ta réponse en 3-5 points numérotés (1), 2), 3)...) + conclusion claire. "
    "Commence OBLIGATOIREMENT par \"OK – \". "
    "N'invente jamais de chiffres. "
    "Tu DOIS fournir une sortie finale exploitable."
)

# Note: Cette solution utilise DIRECTEMENT Chat Completions
# au lieu de l'API Responses qui a le drain de raisonnement
