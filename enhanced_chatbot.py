# enhanced_chatbot.py - Version 7.0 : Agent utilisant une ToolBox externe

import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class BonvinAgent:
    """
    L'Agent est le "Chef de Projet". Il est maintenant agnostique des outils ;
    il reçoit une `toolbox` et une description des outils (`tools_schema`) 
    et se charge de les orchestrer.
    """

    def __init__(self, ai_engine, tools_schema, toolbox):
        self.ai_engine = ai_engine
        self.tools_schema = tools_schema # La description des outils (pour l'IA)
        self.toolbox = toolbox          # L'objet contenant les vraies fonctions Python
        self.system_prompt = """
        Tu es l'analyste expert de la collection privée BONVIN, un "Chef de Projet" doté d'une intelligence de raisonnement supérieure (GPT-4.1).
        Ta mission est de décomposer la question de l'utilisateur en tâches et d'utiliser les "outils" fournis pour trouver les informations nécessaires.

        Processus de pensée :
        1.  Analyse la question de l'utilisateur.
        2.  Décide si tu as besoin d'un outil pour répondre. Si oui, consulte la description des outils et choisis le plus approprié.
        3.  Formule une requête `tool_calls` avec les bons paramètres en te basant sur la description. Tu dois être capable de déduire les bons paramètres à partir de la question. Par exemple, pour "voitures 2 places", tu dois appeler `fetch_collection_items` avec le filtre `{"category": "Voitures", "attribute": "2 places"}`.
        4.  Une fois que tu as le résultat de l'outil, analyse-le et formule la réponse finale pour l'utilisateur.
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
                model="gpt-4o",
                messages=messages,
                tools=self.tools_schema, # On utilise le schéma fourni
                tool_choice="auto",
            )
            response_message = first_response.choices[0].message
            messages.append(response_message)

            # === ÉTAPE 2 : SI L'IA DEMANDE UN OUTIL, ON L'EXÉCUTE ===
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # On cherche la méthode correspondante dans notre objet toolbox
                    function_to_call = getattr(self.toolbox, function_name, None)
                    
                    if not function_to_call:
                        return f"Erreur : L'Agent a tenté d'appeler un outil inconnu '{function_name}'."
                        
                    # Exécution de l'outil avec les bons arguments
                    function_response = function_to_call(filters=function_args)
                    
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response),
                        }
                    )

                # === ÉTAPE 3 : L'IA FORMULE LA RÉPONSE FINALE ===
                second_response = self.ai_engine.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                )
                return second_response.choices[0].message.content.strip()

            return response_message.content.strip()

        except Exception as e:
            logger.error(f"Erreur dans l'exécution de l'agent: {e}", exc_info=True)
            return "Désolé, une erreur de communication est survenue avec le service d'analyse."
