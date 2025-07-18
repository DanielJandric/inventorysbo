# enhanced_chatbot.py - Version 6.0 : Architecture "Agent avec Outils"

import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class BonvinAgent:
    """
    L'Agent est le "Chef de Projet". Il dialogue avec l'IA, interprète ses demandes 
    d'outils et orchestre l'exécution pour obtenir une réponse finale.
    """

    def __init__(self, ai_engine, tools):
        self.ai_engine = ai_engine
        self.tools = tools  # Le catalogue d'outils disponibles
        self.system_prompt = """
        Tu es l'analyste expert de la collection privée BONVIN, un "Chef de Projet" doté d'une intelligence de raisonnement supérieure (GPT-4.1).
        Ta mission n'est pas de répondre directement, mais de décomposer la question de l'utilisateur en tâches et d'utiliser les "outils" fournis pour trouver les informations nécessaires.

        Processus de pensée :
        1.  Analyse la question de l'utilisateur.
        2.  Décide si tu as besoin d'un outil pour répondre. Si oui, lequel ?
        3.  Formule une requête `tool_calls` avec les bons paramètres. Par exemple, pour "voitures allemandes en vente", tu dois appeler l'outil `get_items_from_collection` avec les paramètres `{"category": "Voitures", "attributes": ["allemande", "en vente"]}`.
        4.  Une fois que tu as le résultat de l'outil, analyse-le.
        5.  Si le résultat est suffisant, formule la réponse finale pour l'utilisateur.
        6.  Si tu as besoin de plus d'informations, tu peux appeler un autre outil.
        
        Tu dois raisonner sur les attributs. Par exemple, tu sais qu'une "Porsche GT3" est une voiture "2 places". Utilise cette connaissance pour peupler le paramètre `attributes` de tes appels d'outils.
        """

    def run(self, message: str, history: List[Dict] = None) -> str:
        """
        Exécute le cycle de conversation Agent <-> Outils <-> IA.
        """
        if not self.ai_engine:
            return "Moteur IA indisponible."

        history = history or []
        messages = [{"role": "system", "content": self.system_prompt}] + history + [{"role": "user", "content": message}]

        try:
            # === ÉTAPE 1 : L'IA DÉCIDE D'UNE ACTION ===
            first_response = self.ai_engine.client.chat.completions.create(
                model="gpt-4o", # ou gpt-4.1-turbo
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )
            response_message = first_response.choices[0].message
            messages.append(response_message) # Ajoute la réponse de l'IA à l'historique

            # === ÉTAPE 2 : SI L'IA DEMANDE UN OUTIL, ON L'EXÉCUTE ===
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Chercher la fonction Python correspondante dans le catalogue
                    available_functions = {
                        "get_items_from_collection": self.tools[0]["function"]["executor"]
                    }
                    function_to_call = available_functions.get(function_name)
                    
                    if not function_to_call:
                        return f"Erreur : L'IA a tenté d'appeler un outil inconnu '{function_name}'."
                        
                    # Exécution de l'outil
                    function_response = function_to_call(**function_args)
                    
                    # Ajoute le résultat de l'outil à l'historique
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response),
                        }
                    )

                # === ÉTAPE 3 : L'IA FORMULE LA RÉPONSE FINALE AVEC LE RÉSULTAT DE L'OUTIL ===
                second_response = self.ai_engine.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                )
                return second_response.choices[0].message.content.strip()

            # Si l'IA n'a pas eu besoin d'outil (ex: "bonjour"), on retourne sa réponse directement
            return response_message.content.strip()

        except Exception as e:
            logger.error(f"Erreur dans l'exécution de l'agent: {e}", exc_info=True)
            return "Désolé, une erreur de communication est survenue avec le service d'analyse."
