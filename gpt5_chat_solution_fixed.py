#!/usr/bin/env python3
"""
Solution GPT-5 FIXÉE - Utilise directement Chat Completions
Car l'API Responses a un drain de raisonnement (consomme des tokens mais ne génère pas de texte)
"""

import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI, OpenAIError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT5ChatManagerFixed:
    """Gestionnaire GPT-5 qui utilise directement Chat Completions (qui fonctionne)"""
    
    def __init__(self):
        self.client = OpenAI()
        # Utiliser directement les modèles Chat Completions qui fonctionnent
        self.model_primary = os.getenv("AI_COMPLETIONS_MODEL", "gpt-5-chat-latest")
        self.model_fallback = os.getenv("AI_MODEL_FALLBACK", "gpt-4o")
        self.max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))
        self.timeout = int(os.getenv("TIMEOUT_S", "60"))
        
    def _build_system_prompt(self, custom_prompt: str = "") -> str:
        """Construction du prompt système optimisé pour Chat Completions"""
        base_prompt = (
            "Tu es un analyste marchés expert utilisant GPT-5. "
            "MISSION CRITIQUE : tu DOIS analyser le contexte et émettre une réponse finale en français. "
            "RÈGLE ABSOLUE : "
            "1) ANALYSE d'abord le contexte et la question "
            "2) RAISONNE explicitement sur les données disponibles "
            "3) ÉCRIS ta réponse structurée "
        )
        
        formatting_rules = (
            "Réponds de manière concise, actionnable et contextuelle. "
            "Structure ta réponse en 3-5 points numérotés (1), 2), 3)...) + conclusion claire. "
            "Commence OBLIGATOIREMENT par \"OK – \". "
            "N'invente jamais de chiffres. "
            "Tu DOIS fournir une sortie finale exploitable."
        )
        
        if custom_prompt:
            return f"{base_prompt} {custom_prompt} {formatting_rules}"
        return f"{base_prompt} {formatting_rules}"
    
    def generate_response_direct(self, user_input: str, system_prompt: str = "", context: str = "") -> Dict[str, Any]:
        """
        Génère une réponse en utilisant DIRECTEMENT Chat Completions (qui fonctionne)
        Évite complètement l'API Responses qui a le drain de raisonnement
        """
        try:
            # Construire le contexte complet
            full_input = user_input
            if context:
                full_input = f"Contexte additionnel:\n{context}\n---\n{user_input}"
            
            # Construire le prompt système
            system_content = self._build_system_prompt(system_prompt)
            
            # Appel DIRECT à Chat Completions (pas de fallback nécessaire)
            logger.info(f"🤖 Appel direct Chat Completions avec {self.model_primary}")
            
            response = self.client.chat.completions.create(
                model=self.model_primary,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": (
                        full_input.strip()
                        + "\n\nRéponds en texte brut uniquement. Commence par: OK –"
                    )}
                ],
                max_completion_tokens=min(self.max_tokens, 1000),
                # Pas de temperature pour GPT-5 (utilise la valeur par défaut)
                timeout=self.timeout
            )
            
            content = (response.choices[0].message.content or "").strip()
            
            if content:
                logger.info("✅ Chat Completions réussi")
                return {
                    "response": content,
                    "metadata": {
                        "api": "chat_completions_direct",
                        "model": self.model_primary,
                        "usage": getattr(response, "usage", None),
                        "finish_reason": response.choices[0].finish_reason,
                        "method": "direct_chat_completions"
                    },
                    "success": True
                }
            else:
                logger.warning("⚠️ Chat Completions : contenu vide")
                return {
                    "response": "OK – Besoin de précisions : la génération a échoué. Reformule la question.",
                    "metadata": {"error": "empty_content"},
                    "success": False
                }
                
        except OpenAIError as e:
            logger.error(f"❌ Erreur Chat Completions: {e}")
            return {
                "response": "OK – Erreur technique. Veuillez réessayer.",
                "metadata": {"error": str(e)},
                "success": False
            }
        except Exception as e:
            logger.error(f"❌ Erreur inattendue: {e}")
            return {
                "response": "OK – Erreur système. Contactez le support.",
                "metadata": {"error": str(e)},
                "success": False
            }
    
    def generate_response_with_fallback(self, user_input: str, system_prompt: str = "", context: str = "") -> Dict[str, Any]:
        """
        Version avec fallback vers GPT-4 si GPT-5 échoue
        Mais utilise toujours Chat Completions (pas l'API Responses)
        """
        # Tentative 1: GPT-5 Chat Completions
        result = self.generate_response_direct(user_input, system_prompt, context)
        if result["success"]:
            return result
        
        # Tentative 2: GPT-4 comme fallback
        logger.info(f"🔄 Fallback vers {self.model_fallback}")
        try:
            response = self.client.chat.completions.create(
                model=self.model_fallback,
                messages=[
                    {"role": "system", "content": self._build_system_prompt(system_prompt)},
                    {"role": "user", "content": (
                        f"{context}\n\n{user_input}\n\nRéponds en texte brut. Commence par: OK –"
                    )}
                ],
                max_tokens=min(self.max_tokens, 1000),
                temperature=0.2,
                timeout=self.timeout
            )
            
            content = (response.choices[0].message.content or "").strip()
            if content:
                logger.info("✅ Fallback GPT-4 réussi")
                return {
                    "response": content,
                    "metadata": {
                        "api": "chat_completions_fallback",
                        "model": self.model_fallback,
                        "usage": getattr(response, "usage", None),
                        "method": "fallback_gpt4"
                    },
                    "success": True
                }
        except Exception as e:
            logger.error(f"❌ Erreur fallback GPT-4: {e}")
        
        # Si tout échoue
        return {
            "response": "OK – Service temporairement indisponible. Veuillez réessayer plus tard.",
            "metadata": {"error": "all_methods_failed"},
            "success": False
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Vérification de santé du système"""
        test_input = "Test rapide - dis 'OK' en une phrase."
        
        results = {
            "gpt5_chat": False,
            "gpt4_fallback": False,
            "overall_health": False
        }
        
        # Test GPT-5 Chat Completions
        try:
            result = self.generate_response_direct(test_input, "Tu es un assistant.")
            results["gpt5_chat"] = result["success"] and "OK" in result["response"]
        except:
            pass
        
        # Test GPT-4 fallback
        try:
            result = self.generate_response_with_fallback(test_input, "Tu es un assistant.")
            results["gpt4_fallback"] = result["success"] and "OK" in result["response"]
        except:
            pass
        
        # Santé générale : au moins une méthode fonctionne
        results["overall_health"] = results["gpt5_chat"] or results["gpt4_fallback"]
        
        return results

# Fonction utilitaire pour intégration dans votre app Flask
def get_gpt5_chat_response_fixed(user_input: str, system_prompt: str = "", context: str = "", use_fallback: bool = True) -> Dict[str, Any]:
    """
    Fonction utilitaire pour obtenir une réponse GPT-5 robuste
    Utilise DIRECTEMENT Chat Completions (pas l'API Responses défaillante)
    """
    manager = GPT5ChatManagerFixed()
    
    if use_fallback:
        return manager.generate_response_with_fallback(user_input, system_prompt, context)
    else:
        return manager.generate_response_direct(user_input, system_prompt, context)

# Test simple
if __name__ == "__main__":
    manager = GPT5ChatManagerFixed()
    
    # Test de santé
    print("🔍 VÉRIFICATION DE SANTÉ")
    health = manager.health_check()
    for service, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {status}")
    
    # Test de génération directe (sans fallback)
    print("\n🤖 TEST GÉNÉRATION DIRECTE (Chat Completions)")
    result = manager.generate_response_direct(
        user_input="Quelle est la situation actuelle du marché boursier ?",
        system_prompt="Tu es un analyste financier expert."
    )
    
    print(f"✅ Succès: {result['success']}")
    print(f"🔧 Méthode: {result['metadata']['method']}")
    print(f"📝 Réponse: {result['response'][:200]}...")
    
    # Test avec fallback
    print("\n🔄 TEST AVEC FALLBACK")
    result_fallback = manager.generate_response_with_fallback(
        user_input="Analyse les opportunités sur l'immobilier suisse",
        system_prompt="Tu es un analyste immobilier."
    )
    
    print(f"✅ Succès: {result_fallback['success']}")
    print(f"🔧 Méthode: {result_fallback['metadata']['method']}")
    print(f"📝 Réponse: {result_fallback['response'][:200]}...")
