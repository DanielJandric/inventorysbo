#!/usr/bin/env python3
"""
Solution GPT-5 FINALE - Force la génération de texte avec paramètre text explicite
Basé sur la documentation OpenAI : le paramètre text force la génération de texte
"""

import os
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI, OpenAIError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT5ResponsesForceTextManager:
    """Gestionnaire GPT-5 qui FORCE la génération de texte avec paramètre text explicite"""
    
    def __init__(self):
        self.client = OpenAI()
        self.model = os.getenv("AI_MODEL", "gpt-5")
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))
        self.timeout = int(os.getenv("TIMEOUT_S", "60"))
        self.conversation_history: List[str] = []
        
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
    
    def _extract_text_from_response(self, response) -> Optional[str]:
        """
        Extraction du texte selon la structure de l'API Responses
        """
        try:
            if not hasattr(response, 'output') or not response.output:
                return None
            
            # Parcourir tous les items de output
            for item in response.output:
                if hasattr(item, 'content') and item.content:
                    for content_block in item.content:
                        # Si c'est du texte de sortie
                        if (hasattr(content_block, 'type') and 
                            content_block.type == 'output_text' and
                            hasattr(content_block, 'text') and 
                            content_block.text):
                            
                            return content_block.text.strip()
                        
                        # Si c'est du texte simple
                        elif (hasattr(content_block, 'type') and 
                              content_block.type == 'text' and
                              hasattr(content_block, 'text') and 
                              content_block.text):
                            
                            return content_block.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'extraction du texte: {e}")
            return None
    
    def generate_response_force_text(self, user_input: str, system_prompt: str = "", context: str = "") -> Dict[str, Any]:
        """
        Génère une réponse en FORÇANT la génération de texte avec paramètre text explicite
        """
        try:
            # Construire les instructions système
            instructions = self._build_instructions(system_prompt)
            
            # Préparer l'appel API avec paramètre text EXPLICITE pour forcer la génération
            api_params = {
                "model": self.model,
                "instructions": instructions,
                "input": user_input.strip(),
                "max_output_tokens": self.max_output_tokens,
                "timeout": self.timeout,
                "store": True,  # Stocker pour la gestion du contexte
                # PARAMÈTRE TEXT EXPLICITE pour FORCER la génération de texte
                "text": {
                    "format": {"type": "text"},  # Format de sortie : texte
                    "verbosity": "medium"        # Niveau de détail
                }
            }
            
            # Ajouter le contexte précédent si disponible
            if self.conversation_history:
                api_params["previous_response_id"] = self.conversation_history[-1]
                logger.info(f"🤖 Appel API Responses avec contexte: {self.conversation_history[-1][:10]}...")
            else:
                logger.info(f"🤖 Appel API Responses sans contexte (première conversation)")
            
            logger.info(f"🔧 Paramètre text FORCÉ: {api_params['text']}")
            
            # Appel API Responses avec paramètre text explicite
            response = self.client.responses.create(**api_params)
            
            # Stocker l'ID de cette réponse pour le contexte futur
            if hasattr(response, 'id') and response.id:
                self.conversation_history.append(response.id)
                logger.info(f"💾 Réponse stockée avec ID: {response.id[:10]}...")
            
            # Extraction du texte
            extracted_text = self._extract_text_from_response(response)
            
            if extracted_text:
                logger.info("✅ API Responses réussie avec paramètre text forcé")
                return {
                    "response": extracted_text,
                    "metadata": {
                        "api": "responses_force_text",
                        "model": self.model,
                        "response_id": getattr(response, 'id', None),
                        "previous_context_id": api_params.get("previous_response_id"),
                        "usage": getattr(response, 'usage', None),
                        "method": "responses_api_force_text"
                    },
                    "success": True
                }
            else:
                # Debug de la structure si extraction échoue
                logger.error("❌ Impossible d'extraire du texte malgré le paramètre text forcé")
                logger.info(f"🔍 Structure de la réponse:")
                logger.info(f"  - ID: {getattr(response, 'id', 'N/A')}")
                logger.info(f"  - Status: {getattr(response, 'status', 'N/A')}")
                logger.info(f"  - Output: {getattr(response, 'output', 'N/A')}")
                
                return {
                    "response": "OK – Erreur : impossible d'extraire la réponse de l'API.",
                    "metadata": {
                        "api": "responses_force_text",
                        "model": self.model,
                        "error": "no_text_extracted_despite_force",
                        "response_id": getattr(response, 'id', None),
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
        Mais essaie d'abord Responses avec paramètre text forcé
        """
        # Tentative 1: API Responses avec paramètre text forcé
        result = self.generate_response_force_text(user_input, system_prompt, context)
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
    
    def clear_conversation_history(self):
        """Efface l'historique de conversation"""
        self.conversation_history.clear()
        logger.info("🗑️ Historique de conversation effacé")
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Retourne le contexte de conversation actuel"""
        return {
            "conversation_length": len(self.conversation_history),
            "last_response_id": self.conversation_history[-1] if self.conversation_history else None,
            "all_response_ids": self.conversation_history.copy()
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
            result = self.generate_response_force_text(test_input, "Tu es un assistant.")
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
def get_gpt5_response_force_text(user_input: str, system_prompt: str = "", context: str = "", use_fallback: bool = True) -> Dict[str, Any]:
    """
    Fonction utilitaire pour obtenir une réponse GPT-5 via l'API Responses
    Avec paramètre text forcé pour garantir la génération de texte
    """
    manager = GPT5ResponsesForceTextManager()
    
    if use_fallback:
        return manager.generate_response_with_fallback(user_input, system_prompt, context)
    else:
        return manager.generate_response_force_text(user_input, system_prompt, context)

# Test simple
if __name__ == "__main__":
    manager = GPT5ResponsesForceTextManager()
    
    # Test de santé
    print("🔍 VÉRIFICATION DE SANTÉ")
    health = manager.health_check()
    for service, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {status}")
    
    # Test de génération via API Responses avec paramètre text forcé
    print("\n🤖 TEST API RESPONSES AVEC PARAMÈTRE TEXT FORCÉ")
    result = manager.generate_response_force_text(
        user_input="Quelle est la situation actuelle du marché boursier ?",
        system_prompt="Tu es un analyste financier expert."
    )
    
    print(f"✅ Succès: {result['success']}")
    if result['success']:
        print(f"🔧 Méthode: {result['metadata']['method']}")
        print(f"📝 Réponse: {result['response'][:200]}...")
        print(f"🆔 ID Réponse: {result['metadata']['response_id'][:20]}...")
    else:
        print(f"❌ Erreur: {result['metadata'].get('error', 'Unknown')}")
    
    # Test de conversation avec contexte
    print("\n💬 TEST CONVERSATION AVEC CONTEXTE")
    follow_up = manager.generate_response_force_text(
        user_input="Et quelles sont les opportunités sur l'immobilier ?",
        system_prompt="Tu es un analyste immobilier."
    )
    
    print(f"✅ Succès: {follow_up['success']}")
    if follow_up['success']:
        print(f"🔧 Méthode: {follow_up['metadata']['method']}")
        print(f"📝 Réponse: {follow_up['response'][:200]}...")
        print(f"🆔 ID Réponse: {follow_up['metadata']['response_id'][:20]}...")
        print(f"🔗 Contexte précédent: {follow_up['metadata']['previous_context_id'][:20]}...")
    
    # Afficher le contexte de conversation
    print("\n📚 CONTEXTE DE CONVERSATION")
    context = manager.get_conversation_context()
    print(f"  Longueur: {context['conversation_length']}")
    print(f"  Dernier ID: {context['last_response_id'][:20] if context['last_response_id'] else 'Aucun'}...")
    
    # Test avec fallback
    print("\n🔄 TEST AVEC FALLBACK")
    result_fallback = manager.generate_response_with_fallback(
        user_input="Analyse les opportunités sur l'immobilier suisse",
        system_prompt="Tu es un analyste immobilier."
    )
    
    print(f"✅ Succès: {result_fallback['success']}")
    if result_fallback['success']:
        print(f"🔧 Méthode: {result_fallback['metadata']['method']}")
        print(f"📝 Réponse: {result_fallback['response'][:200]}...")
