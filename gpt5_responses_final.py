#!/usr/bin/env python3
"""
Solution GPT-5 FINALE - Utilise CORRECTEMENT l'API Responses
Avec paramètres text explicites pour forcer la génération de texte
"""

import os
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI, OpenAIError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT5ResponsesFinalManager:
    """Gestionnaire GPT-5 utilisant CORRECTEMENT l'API Responses avec paramètres text explicites"""
    
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
    
    def generate_response_final(self, user_input: str, system_prompt: str = "", context: str = "") -> Dict[str, Any]:
        """
        Génère une réponse en utilisant CORRECTEMENT l'API Responses
        Avec paramètres text explicites pour forcer la génération de texte
        """
        try:
            # Construire les instructions système
            instructions = self._build_instructions(system_prompt)
            
            # Préparer l'appel API avec paramètres text EXPLICITES
            api_params = {
                "model": self.model,
                "instructions": instructions,
                "input": user_input.strip(),
                "max_output_tokens": self.max_output_tokens,
                "timeout": self.timeout,
                "store": True,  # Stocker pour la gestion du contexte
                # PARAMÈTRES TEXT EXPLICITES pour forcer la génération de texte
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
            
            logger.info(f"🔧 Paramètres text: {api_params['text']}")
            
            # Appel CORRECT selon la documentation OpenAI
            response = self.client.responses.create(**api_params)
            
            # Stocker l'ID de cette réponse pour le contexte futur
            if hasattr(response, 'id') and response.id:
                self.conversation_history.append(response.id)
                logger.info(f"💾 Réponse stockée avec ID: {response.id[:10]}...")
            
            # Extraction du texte selon la documentation
            output_text = getattr(response, 'output_text', None)
            
            if output_text and output_text.strip():
                logger.info("✅ API Responses réussie avec output_text")
                return {
                    "response": output_text.strip(),
                    "metadata": {
                        "api": "responses_final",
                        "model": self.model,
                        "response_id": getattr(response, 'id', None),
                        "previous_context_id": api_params.get("previous_response_id"),
                        "usage": getattr(response, 'usage', None),
                        "method": "responses_api_text_explicit"
                    },
                    "success": True
                }
            else:
                # Si output_text est vide, explorer la structure de sortie
                logger.warning("⚠️ output_text vide, exploration de la structure...")
                
                # Debug de la structure complète
                logger.info(f"🔍 Structure de la réponse:")
                logger.info(f"  - ID: {getattr(response, 'id', 'N/A')}")
                logger.info(f"  - Status: {getattr(response, 'status', 'N/A')}")
                logger.info(f"  - Output: {getattr(response, 'output', 'N/A')}")
                
                if hasattr(response, 'output') and response.output:
                    logger.info(f"  - Nombre d'items output: {len(response.output)}")
                    
                    # Explorer chaque item de sortie
                    for i, item in enumerate(response.output):
                        logger.info(f"    Item {i}:")
                        logger.info(f"      - Type: {getattr(item, 'type', 'N/A')}")
                        logger.info(f"      - Role: {getattr(item, 'role', 'N/A')}")
                        
                        if hasattr(item, 'content') and item.content:
                            logger.info(f"      - Nombre d'items content: {len(item.content)}")
                            
                            for j, content_item in enumerate(item.content):
                                logger.info(f"        Content {j}:")
                                logger.info(f"          - Type: {getattr(content_item, 'type', 'N/A')}")
                                logger.info(f"          - Text: {getattr(content_item, 'text', 'N/A')}")
                                
                                # Essayer d'extraire le texte
                                if (hasattr(content_item, 'type') and 
                                    content_item.type == 'output_text' and
                                    hasattr(content_item, 'text') and 
                                    content_item.text):
                                    
                                    logger.info("✅ Texte extrait de la structure de sortie")
                                    return {
                                        "response": content_item.text.strip(),
                                        "metadata": {
                                            "api": "responses_final",
                                            "model": self.model,
                                            "response_id": getattr(response, 'id', None),
                                            "previous_context_id": api_params.get("previous_response_id"),
                                            "usage": getattr(response, 'usage', None),
                                            "method": "responses_api_structure_extraction"
                                        },
                                        "success": True
                                    }
                
                # Si toujours rien, retourner l'erreur avec debug
                logger.error("❌ Impossible d'extraire du texte de l'API Responses")
                return {
                    "response": "OK – Erreur : impossible d'extraire la réponse de l'API.",
                    "metadata": {
                        "api": "responses_final",
                        "model": self.model,
                        "error": "no_text_extracted",
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
        Mais essaie d'abord Responses correctement avec paramètres text explicites
        """
        # Tentative 1: API Responses avec paramètres text explicites
        result = self.generate_response_final(user_input, system_prompt, context)
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
            result = self.generate_response_final(test_input, "Tu es un assistant.")
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
def get_gpt5_response_final(user_input: str, system_prompt: str = "", context: str = "", use_fallback: bool = True) -> Dict[str, Any]:
    """
    Fonction utilitaire pour obtenir une réponse GPT-5 via l'API Responses
    Avec paramètres text explicites pour forcer la génération de texte
    """
    manager = GPT5ResponsesFinalManager()
    
    if use_fallback:
        return manager.generate_response_with_fallback(user_input, system_prompt, context)
    else:
        return manager.generate_response_final(user_input, system_prompt, context)

# Test simple
if __name__ == "__main__":
    manager = GPT5ResponsesFinalManager()
    
    # Test de santé
    print("🔍 VÉRIFICATION DE SANTÉ")
    health = manager.health_check()
    for service, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {status}")
    
    # Test de génération via API Responses avec paramètres text explicites
    print("\n🤖 TEST API RESPONSES AVEC PARAMÈTRES TEXT EXPLICITES")
    result = manager.generate_response_final(
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
    follow_up = manager.generate_response_final(
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
