#!/usr/bin/env python3
"""
Solution robuste pour le chat GPT-5
Basée sur la stratégie fallback qui fonctionne dans gpt5_responses_mvp.py
"""

import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI, OpenAIError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT5ChatManager:
    """Gestionnaire de chat GPT-5 avec fallback robuste"""
    
    def __init__(self):
        self.client = OpenAI()
        self.model_primary = os.getenv("MODEL_PRIMARY", "gpt-5")
        self.model_secondary = os.getenv("MODEL_SECONDARY", "gpt-5-2025-08-07") 
        self.model_fallback = os.getenv("MODEL_FALLBACK", "gpt-5-chat-latest")
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))
        self.timeout = int(os.getenv("TIMEOUT_S", "60"))
        
    def _build_instructions(self, system_prompt: str) -> str:
        """Construction des instructions optimisées"""
        base_instructions = (
            "Tu es un analyste marchés expert utilisant GPT-5. "
            "MISSION CRITIQUE : tu DOIS raisonner explicitement puis émettre une réponse finale en français. "
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
        
        return f"{base_instructions} {system_prompt} {formatting_rules}"
    
    def _try_responses_api(self, instructions: str, user_input: str, model: str) -> tuple[str, Dict[str, Any]]:
        """Tentative avec l'API Responses"""
        try:
            logger.info(f"🤖 Tentative Responses API avec {model}")
            
            enhanced_input = (
                user_input.strip()
                + "\n\nÉcris la RÉPONSE FINALE maintenant en texte brut, 3–5 lignes numérotées, puis une conclusion. "
                  "Commence par: OK –"
            )
            
            response = self.client.responses.create(
                model=model,
                instructions=instructions,
                input=enhanced_input,
                tool_choice="none",
                text={"format": {"type": "text"}, "verbosity": "medium"},
                max_output_tokens=self.max_output_tokens,
                timeout=self.timeout
                # ⚠️ PAS de paramètre reasoning pour éviter le drain
            )
            
            output_text = (response.output_text or "").strip()
            metadata = {
                "api": "responses",
                "model": model,
                "request_id": getattr(response, "_request_id", None),
                "usage": getattr(response, "usage", None),
                "status": getattr(response, "status", None)
            }
            
            if output_text:
                logger.info(f"✅ Responses API réussie avec {model}")
                return output_text, metadata
            else:
                logger.warning(f"⚠️ Responses API {model} : output_text vide")
                return "", metadata
                
        except Exception as e:
            logger.error(f"❌ Erreur Responses API {model}: {e}")
            return "", {"api": "responses", "model": model, "error": str(e)}
    
    def _try_chat_completions(self, system_prompt: str, user_input: str) -> tuple[str, Dict[str, Any]]:
        """Fallback avec Chat Completions (la méthode qui fonctionne)"""
        try:
            logger.info(f"🔄 Fallback Chat Completions avec {self.model_fallback}")
            
            enhanced_user_input = (
                user_input.strip()
                + "\n\nRéponds en texte brut uniquement. Commence par: OK –"
            )
            
            response = self.client.chat.completions.create(
                model=self.model_fallback,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_user_input}
                ],
                max_completion_tokens=min(self.max_output_tokens, 1000),
                # Pas de temperature pour GPT-5
                timeout=self.timeout
            )
            
            content = (response.choices[0].message.content or "").strip()
            metadata = {
                "api": "chat_completions",
                "model": self.model_fallback,
                "usage": getattr(response, "usage", None),
                "finish_reason": response.choices[0].finish_reason
            }
            
            if content:
                logger.info("✅ Chat Completions réussi")
                return content, metadata
            else:
                logger.warning("⚠️ Chat Completions : contenu vide")
                return "", metadata
                
        except Exception as e:
            logger.error(f"❌ Erreur Chat Completions: {e}")
            return "", {"api": "chat_completions", "error": str(e)}
    
    def generate_response(self, user_input: str, system_prompt: str = "", context: str = "") -> Dict[str, Any]:
        """
        Génère une réponse avec stratégie de fallback robuste
        
        Args:
            user_input: Question de l'utilisateur
            system_prompt: Prompt système personnalisé (optionnel)
            context: Contexte additionnel (optionnel)
            
        Returns:
            Dict avec 'response', 'metadata', 'success'
        """
        # Construire le contexte complet
        full_input = user_input
        if context:
            full_input = f"Contexte additionnel:\n{context}\n---\n{user_input}"
        
        # Instructions pour Responses API
        instructions = self._build_instructions(system_prompt)
        
        # Stratégie de fallback : exactement comme votre script qui fonctionne
        
        # Tentative 1: Modèle principal
        response_text, metadata = self._try_responses_api(instructions, full_input, self.model_primary)
        if response_text:
            return {
                "response": response_text,
                "metadata": metadata,
                "success": True,
                "method": "responses_primary"
            }
        
        # Tentative 2: Modèle secondaire
        response_text, metadata = self._try_responses_api(instructions, full_input, self.model_secondary)
        if response_text:
            return {
                "response": response_text,
                "metadata": metadata,
                "success": True,
                "method": "responses_secondary"
            }
        
        # Fallback : Chat Completions (la méthode qui fonctionne TOUJOURS)
        response_text, metadata = self._try_chat_completions(system_prompt, full_input)
        if response_text:
            return {
                "response": response_text,
                "metadata": metadata,
                "success": True,
                "method": "chat_completions_fallback"
            }
        
        # Si tout échoue
        fallback_message = "OK – Besoin de précisions : la génération de réponse a échoué. Reformule la question en une phrase claire."
        return {
            "response": fallback_message,
            "metadata": {"error": "all_methods_failed"},
            "success": False,
            "method": "fallback_message"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Vérification de santé du système"""
        test_input = "Test rapide"
        
        results = {
            "responses_primary": False,
            "responses_secondary": False,
            "chat_fallback": False,
            "overall_health": False
        }
        
        # Test Responses API primaire
        try:
            text, _ = self._try_responses_api("Tu es un assistant.", test_input, self.model_primary)
            results["responses_primary"] = bool(text)
        except:
            pass
        
        # Test Responses API secondaire
        try:
            text, _ = self._try_responses_api("Tu es un assistant.", test_input, self.model_secondary)
            results["responses_secondary"] = bool(text)
        except:
            pass
        
        # Test Chat Completions (fallback)
        try:
            text, _ = self._try_chat_completions("Tu es un assistant.", test_input)
            results["chat_fallback"] = bool(text)
        except:
            pass
        
        # Santé générale : au moins une méthode fonctionne
        results["overall_health"] = any([
            results["responses_primary"],
            results["responses_secondary"], 
            results["chat_fallback"]
        ])
        
        return results

# Fonction utilitaire pour intégration dans votre app Flask
def get_gpt5_chat_response(user_input: str, system_prompt: str = "", context: str = "") -> Dict[str, Any]:
    """
    Fonction utilitaire pour obtenir une réponse GPT-5 robuste
    Compatible avec votre système Flask existant
    """
    manager = GPT5ChatManager()
    return manager.generate_response(user_input, system_prompt, context)

# Test simple
if __name__ == "__main__":
    manager = GPT5ChatManager()
    
    # Test de santé
    print("🔍 VÉRIFICATION DE SANTÉ")
    health = manager.health_check()
    for service, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {status}")
    
    # Test de génération
    print("\n🤖 TEST DE GÉNÉRATION")
    result = manager.generate_response(
        user_input="Quelle est la situation actuelle du marché boursier ?",
        system_prompt="Tu es un analyste financier expert."
    )
    
    print(f"✅ Succès: {result['success']}")
    print(f"🔧 Méthode: {result['method']}")
    print(f"📝 Réponse: {result['response']}")
