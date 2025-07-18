# enhanced_chatbot.py - Version 6.0 : Agent avec Outils

import logging
import json
from typing import Dict, List, Any
from tools import ToolBox # <-- Importer la boîte à outils

logger = logging.getLogger(__name__)

class EnhancedChatbot:
    """
    Agent IA qui raisonne sur les outils à utiliser pour répondre à une question.
    """

    def __init__(self, data_manager, ai_engine):
        self.data_manager = data_manager
        self.ai_engine = ai_engine
        self.toolbox = ToolBox(data_manager) # <-- L'agent possède sa propre boîte à outils

    def process_message(self, message: str, history: List[Dict] = None) -> str:
        """
        Orchestre le raisonnement de l'agent en plusieurs étapes.
        """
        history = history or []
        try:
            # Étape 1: Demander à l'IA de choisir un outil
            tool_choice_instruction = self._choose_tool(message, history)
            
            # Si l'IA ne choisit pas d'outil et répond directement
            if "tool_to_use" not in tool_choice_instruction:
                return tool_choice_instruction.get("final_answer", "Je ne suis pas sûr de savoir comment répondre à cela.")

            # Étape 2: Exécuter l'outil choisi
            tool_name = tool_choice_instruction["tool_to_use"]
            tool_parameters = tool_choice_instruction["parameters"]
            tool_result = self._execute_tool(tool_name, tool_parameters)

            # Étape 3: Fournir le résultat de l'outil à l'IA pour la réponse finale
            return self._generate_final_response(message, tool_result)

        except Exception as e:
            logger.error(f"Erreur critique dans le traitement de l'agent: {e}", exc_info=True)
            return "Désolé, une erreur interne m'empêche de traiter votre demande."

    def _choose_tool(self, message: str, history: List[Dict]) -> Dict:
        """Première passe : l'IA analyse la question et choisit un outil à utiliser."""
        system_prompt = """
        Tu es un chef de projet expert. Ton rôle est de choisir le bon outil pour répondre à la demande de l'utilisateur.
        Ne réponds PAS à la question. Ta seule mission est de fournir un JSON décrivant l'outil et les paramètres à utiliser.
        Si aucun outil ne semble approprié, tu peux répondre directement à la question avec une clé "final_answer".
        """

        user_prompt = f"""
        Historique de la conversation : {history[-3:] if history else "Aucun"}
        
        Question de l'utilisateur : "{message}"
        
        Outils disponibles :
        ```json
        {json.dumps(self.toolbox.get_available_tools(), indent=2)}
        ```
        
        En te basant sur la question, quel outil dois-je utiliser ? Fournis ta réponse au format JSON avec les clés "tool_to_use" et "parameters".
        """

        response = self.ai_engine.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            logger.error("L'IA n'a pas retourné un JSON valide pour le choix de l'outil.")
            return {"final_answer": "Je n'ai pas compris comment traiter votre demande."}


    def _execute_tool(self, tool_name: str, parameters: dict) -> Any:
        """Exécute l'outil demandé par l'IA."""
        if hasattr(self.toolbox, tool_name):
            tool_function = getattr(self.toolbox, tool_name)
            return tool_function(**parameters)
        else:
            return f"Erreur : L'outil '{tool_name}' n'existe pas."

    def _generate_final_response(self, original_message: str, tool_result: Any) -> str:
        """Deuxième passe : l'IA reçoit le résultat de l'outil et formule la réponse finale."""
        system_prompt = """
        Tu es l'assistant expert de la collection BONVIN. Tu es un communicant brillant.
        Ton rôle est de transformer des données brutes (le résultat d'un outil) en une réponse naturelle, claire et professionnelle.
        """

        user_prompt = f"""
        La question originale de l'utilisateur était : "{original_message}"
        
        Mon assistant a utilisé un outil et a obtenu le résultat suivant :
        ```json
        {json.dumps(tool_result, indent=2, default=str)}
        ```
        
        En te basant sur la question originale et ce résultat, formule la réponse finale pour l'utilisateur.
        Sois concis et direct. Si tu donnes une liste, ne montre que les 5-10 premiers résultats si elle est longue.
        """

        response = self.ai_engine.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
