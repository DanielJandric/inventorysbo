#!/usr/bin/env python3
"""
Solution GPT-5 CORRECTE - Extraction du texte selon la VRAIE structure de l'API Responses
Basé sur l'analyse de ChatGPT : le texte est dans response.output[].content[].text
"""

import os
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI, OpenAIError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT5ResponsesExtractionManager:
    """Gestionnaire GPT-5 avec extraction CORRECTE du texte selon la vraie structure de l'API"""
    
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
        Extraction CORRECTE du texte selon la vraie structure de l'API Responses
        Basé sur l'analyse de ChatGPT : response.output[].content[].text
        """
        try:
            # Vérifier si response.output existe
            if not hasattr(response, 'output') or not response.output:
                logger.warning("⚠️ Pas de champ 'output' dans la réponse")
                return None
            
            logger.info(f"🔍 Exploration de {len(response.output)} items dans output")
            
            # Parcourir tous les items de output
            for i, item in enumerate(response.output):
                logger.info(f"  Item {i}: type={getattr(item, 'type', 'N/A')}, role={getattr(item, 'role', 'N/A')}")
                
                # Vérifier si l'item a du contenu
                if hasattr(item, 'content') and item.content:
                    logger.info(f"    Contenu trouvé: {len(item.content)} blocs")
                    
                    # Parcourir tous les blocs de contenu
                    for j, content_block in enumerate(item.content):
                        logger.info(f"      Bloc {j}: type={getattr(content_block, 'type', 'N/A')}")
                        
                        # Si c'est du texte de sortie
                        if (hasattr(content_block, 'type') and 
                            content_block.type == 'output_text' and
                            hasattr(content_block, 'text') and 
                            content_block.text):
                            
                            logger.info(f"✅ Texte extrait du bloc {j}: {content_block.text[:50]}...")
                            return content_block.text.strip()
                        
                        # Si c'est du texte simple
                        elif (hasattr(content_block, 'type') and 
                              content_block.type == 'text' and
                              hasattr(content_block, 'text') and 
                              content_block.text):
                            
                            logger.info(f"✅ Texte simple extrait du bloc {j}: {content_block.text[:50]}...")
                            return content_block.text.strip()
                        
                        # Si c'est du contenu de message
                        elif (hasattr(content_block, 'type') and 
                              content_block.type == 'message' and
                              hasattr(content_block, 'text') and 
                              content_block.text):
                            
                            logger.info(f"✅ Message extrait du bloc {j}: {content_block.text[:50]}...")
                            return content_block.text.strip()
            
            logger.warning("⚠️ Aucun texte trouvé dans la structure de réponse")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'extraction du texte: {e}")
            return None
    
    def generate_response_correct_extraction(self, user_input: str, system_prompt: str = "", context: str = "") -> Dict[str, Any]:
        """
        Génère une réponse en utilisant CORRECTEMENT l'API Responses
        Avec extraction CORRECTE du texte selon la vraie structure
        """
        try:
            # Construire les instructions système
            instructions = self._build_instructions(system_prompt)
            
            # Préparer l'appel API
            api_params = {
                "model": self.model,
                "instructions": instructions,
                "input": user_input.strip(),
                "max_output_tokens": self.max_output_tokens,
                "timeout": self.timeout,
                "store": True,  # Stocker pour la gestion du contexte
            }
            
            # Ajouter le contexte précédent si disponible
            if self.conversation_history:
                api_params["previous_response_id"] = self.conversation_history[-1]
                logger.info(f"🤖 Appel API Responses avec contexte: {self.conversation_history[-1][:10]}...")
            else:
                logger.info(f"🤖 Appel API Responses sans contexte (première conversation)")
            
            # Appel API Responses
            response = self.client.responses.create(**api_params)
            
            # Stocker l'ID de cette réponse pour le contexte futur
            if hasattr(response, 'id') and response.id:
                self.conversation_history.append(response.id)
                logger.info(f"💾 Réponse stockée avec ID: {response.id[:10]}...")
            
            # Extraction CORRECTE du texte selon la vraie structure
            extracted_text = self._extract_text_from_response(response)
            
            if extracted_text:
                logger.info("✅ API Responses réussie avec extraction correcte")
                return {
                    "response": extracted_text,
                    "metadata": {
                        "api": "responses_correct_extraction",
                        "model": self.model,
                        "response_id": getattr(response, 'id', None),
                        "previous_context_id": api_params.get("previous_response_id"),
                        "usage": getattr(response, 'usage', None),
                        "method": "responses_api_correct_extraction"
                    },
                    "success": True
                }
            else:
                # Debug de la structure complète si extraction échoue
                logger.error("❌ Impossible d'extraire du texte de l'API Responses")
                logger.info(f"🔍 Structure complète de la réponse:")
                logger.info(f"  - ID: {getattr(response, 'id', 'N/A')}")
                logger.info(f"  - Status: {getattr(response, 'status', 'N/A')}")
                logger.info(f"  - Output: {getattr(response, 'output', 'N/A')}")
                
                return {
                    "response": "OK – Erreur : impossible d'extraire la réponse de l'API.",
                    "metadata": {
                        "api": "responses_correct_extraction",
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
        Mais essaie d'abord Responses avec extraction correcte
        """
        # Tentative 1: API Responses avec extraction correcte
        result = self.generate_response_correct_extraction(user_input, system_prompt, context)
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
            result = self.generate_response_correct_extraction(test_input, "Tu es un assistant.")
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
def get_gpt5_response_correct_extraction(user_input: str, system_prompt: str = "", context: str = "", use_fallback: bool = True) -> Dict[str, Any]:
    """
    Fonction utilitaire pour obtenir une réponse GPT-5 via l'API Responses
    Avec extraction CORRECTE du texte selon la vraie structure
    """
    manager = GPT5ResponsesExtractionManager()
    
    if use_fallback:
        return manager.generate_response_with_fallback(user_input, system_prompt, context)
    else:
        return manager.generate_response_correct_extraction(user_input, system_prompt, context)

# Test simple
if __name__ == "__main__":
    manager = GPT5ResponsesExtractionManager()
    
    # Test de santé
    print("🔍 VÉRIFICATION DE SANTÉ")
    health = manager.health_check()
    for service, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {status}")
    
    # Test de génération via API Responses avec extraction correcte
    print("\n🤖 TEST API RESPONSES AVEC EXTRACTION CORRECTE")
    result = manager.generate_response_correct_extraction(
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
    follow_up = manager.generate_response_correct_extraction(
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
