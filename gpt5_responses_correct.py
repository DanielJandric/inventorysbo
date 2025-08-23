#!/usr/bin/env python3
"""
Solution GPT-5 CORRECTE - Utilise l'API Responses comme prévu par OpenAI
Basé sur la documentation officielle OpenAI
"""

import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI, OpenAIError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT5ResponsesManager:
    """Gestionnaire GPT-5 utilisant CORRECTEMENT l'API Responses"""
    
    def __init__(self):
        self.client = OpenAI()
        # Utiliser gpt-5 comme prévu par OpenAI
        self.model = os.getenv("AI_MODEL", "gpt-5")
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))
        self.timeout = int(os.getenv("TIMEOUT_S", "60"))
        
    def _build_instructions(self, custom_prompt: str = "") -> str:
        """Construction des instructions selon la documentation OpenAI"""
        base_instructions = (
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
            return f"{base_instructions} {custom_prompt} {formatting_rules}"
        return f"{base_instructions} {formatting_rules}"
    
    def generate_response_responses_api(self, user_input: str, system_prompt: str = "", context: str = "") -> Dict[str, Any]:
        """
        Génère une réponse en utilisant CORRECTEMENT l'API Responses
        Selon la documentation OpenAI officielle
        """
        try:
            # Construire le contexte complet
            full_input = user_input
            if context:
                full_input = f"Contexte additionnel:\n{context}\n---\n{user_input}"
            
            # Construire les instructions système
            instructions = self._build_instructions(system_prompt)
            
            logger.info(f"🤖 Appel API Responses avec {self.model}")
            
            # Appel CORRECT selon la documentation OpenAI
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,  # Instructions au niveau top-level
                input=full_input.strip(),  # Input simple (string)
                max_output_tokens=self.max_output_tokens,
                timeout=self.timeout,
                # Paramètres optionnels pour améliorer la qualité
                text={
                    "format": {"type": "text"},  # Format de sortie structuré
                    "verbosity": "medium"  # Niveau de détail
                }
            )
            
            # Extraction du texte selon la documentation
            output_text = getattr(response, 'output_text', None)
            
            if output_text and output_text.strip():
                logger.info("✅ API Responses réussie")
                return {
                    "response": output_text.strip(),
                    "metadata": {
                        "api": "responses",
                        "model": self.model,
                        "response_id": getattr(response, 'id', None),
                        "usage": getattr(response, 'usage', None),
                        "method": "responses_api_correct"
                    },
                    "success": True
                }
            else:
                # Si output_text est vide, vérifier la structure de sortie
                logger.warning("⚠️ output_text vide, vérification de la structure...")
                
                if hasattr(response, 'output') and response.output:
                    # Explorer la structure de sortie
                    for item in response.output:
                        if hasattr(item, 'type') and item.type == 'message':
                            if hasattr(item, 'content') and item.content:
                                for content_item in item.content:
                                    if hasattr(content_item, 'type') and content_item.type == 'output_text':
                                        if hasattr(content_item, 'text') and content_item.text:
                                            logger.info("✅ Texte extrait de la structure de sortie")
                                            return {
                                                "response": content_item.text.strip(),
                                                "metadata": {
                                                    "api": "responses",
                                                    "model": self.model,
                                                    "response_id": getattr(response, 'id', None),
                                                    "usage": getattr(response, 'usage', None),
                                                    "method": "responses_api_structure_extraction"
                                                },
                                                "success": True
                                            }
                
                # Si toujours rien, retourner l'erreur
                logger.error("❌ Impossible d'extraire du texte de l'API Responses")
                return {
                    "response": "OK – Erreur : impossible d'extraire la réponse de l'API.",
                    "metadata": {
                        "api": "responses",
                        "model": self.model,
                        "error": "no_text_extracted",
                        "response_structure": str(getattr(response, 'output', 'N/A'))
                    },
                    "success": False
                }
                
        except OpenAIError as e:
            logger.error(f"❌ Erreur API Responses: {e}")
            return {
                "response": "OK – Erreur technique de l'API. Veuillez réessayer.",
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
        Version avec fallback vers Chat Completions si Responses échoue
        Mais essaie d'abord Responses correctement
        """
        # Tentative 1: API Responses (correctement implémentée)
        result = self.generate_response_responses_api(user_input, system_prompt, context)
        if result["success"]:
            return result
        
        # Tentative 2: Chat Completions comme fallback
        logger.info(f"🔄 Fallback vers Chat Completions")
        try:
            response = self.client.chat.completions.create(
                model="gpt-5-chat-latest",
                messages=[
                    {"role": "system", "content": self._build_instructions(system_prompt)},
                    {"role": "user", "content": (
                        f"{context}\n\n{user_input}\n\nRéponds en texte brut. Commence par: OK –"
                    )}
                ],
                max_completion_tokens=min(self.max_output_tokens, 1000),
                timeout=self.timeout
            )
            
            content = (response.choices[0].message.content or "").strip()
            if content:
                logger.info("✅ Fallback Chat Completions réussi")
                return {
                    "response": content,
                    "metadata": {
                        "api": "chat_completions_fallback",
                        "model": "gpt-5-chat-latest",
                        "usage": getattr(response, "usage", None),
                        "method": "fallback_chat_completions"
                    },
                    "success": True
                }
        except Exception as e:
            logger.error(f"❌ Erreur fallback Chat Completions: {e}")
        
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
            "responses_api": False,
            "chat_fallback": False,
            "overall_health": False
        }
        
        # Test API Responses
        try:
            result = self.generate_response_responses_api(test_input, "Tu es un assistant.")
            results["responses_api"] = result["success"] and "OK" in result["response"]
        except:
            pass
        
        # Test Chat Completions fallback
        try:
            result = self.generate_response_with_fallback(test_input, "Tu es un assistant.")
            results["chat_fallback"] = result["success"] and "OK" in result["response"]
        except:
            pass
        
        # Santé générale : au moins une méthode fonctionne
        results["overall_health"] = results["responses_api"] or results["chat_fallback"]
        
        return results

# Fonction utilitaire pour intégration dans votre app Flask
def get_gpt5_response_correct(user_input: str, system_prompt: str = "", context: str = "", use_fallback: bool = True) -> Dict[str, Any]:
    """
    Fonction utilitaire pour obtenir une réponse GPT-5 via l'API Responses
    Utilise CORRECTEMENT l'API selon la documentation OpenAI
    """
    manager = GPT5ResponsesManager()
    
    if use_fallback:
        return manager.generate_response_with_fallback(user_input, system_prompt, context)
    else:
        return manager.generate_response_responses_api(user_input, system_prompt, context)

# Test simple
if __name__ == "__main__":
    manager = GPT5ResponsesManager()
    
    # Test de santé
    print("🔍 VÉRIFICATION DE SANTÉ")
    health = manager.health_check()
    for service, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {status}")
    
    # Test de génération via API Responses
    print("\n🤖 TEST API RESPONSES (correctement implémentée)")
    result = manager.generate_response_responses_api(
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
