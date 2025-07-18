# enhanced_chatbot.py - Version 4.0 : Programmation Orientée Prompt

import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class EnhancedChatbot:
    """
    Chatbot V4 : l'IA est le pilote, le code est le co-pilote.
    Le code rassemble un maximum de contexte pertinent et le structure dans un 
    "Prompt Maître" pour que l'IA puisse raisonner avec toute sa puissance.
    """

    def __init__(self, data_manager, ai_engine):
        self.data_manager = data_manager
        self.ai_engine = ai_engine

    def process_message(self, message: str, history: List[Dict] = None) -> str:
        """
        Orchestre la construction du Prompt Maître et interroge l'IA.
        """
        history = history or []
        try:
            # Étape 1: Construire le contexte de manière systématique
            # On ne devine plus, on collecte tout ce qui pourrait être utile.
            full_context = self._build_comprehensive_context(message)

            # Étape 2: Construire le Prompt Maître Dynamique
            master_prompt = self._build_master_prompt(message, full_context, history)

            # Étape 3: Laisser l'IA raisonner
            return self._query_ai_model(master_prompt)

        except Exception as e:
            logger.error(f"Erreur critique dans le traitement du chatbot pour le message: '{message}'", exc_info=True)
            return "Désolé, une erreur technique m'empêche de traiter votre demande. L'équipe a été notifiée."

    def _build_comprehensive_context(self, message: str) -> Dict:
        """
        Rassemble systématiquement plusieurs types d'informations pour chaque requête.
        C'est le travail du "co-pilote" : préparer le tableau de bord pour le pilote (IA).
        """
        all_items = self.data_manager.fetch_all_items()
        
        # 1. Toujours effectuer une recherche sémantique
        semantic_results = self.ai_engine.semantic_search.semantic_search(message, all_items, top_k=5)
        
        # 2. Toujours calculer les statistiques clés
        analytics = self.data_manager.calculate_advanced_analytics(all_items)
        
        # 3. Mettre en forme le contexte
        context = {
            "semantic_search": {
                "summary": f"{len(semantic_results)} objets trouvés avec une pertinence sémantique.",
                "items": [item.to_dict() for item, score in semantic_results]
            },
            "analytics_summary": {
                "total_items": analytics.get('basic_metrics', {}).get('total_items', 0),
                "portfolio_value": analytics.get('financial_metrics', {}).get('portfolio_value', 0),
                "sales_pipeline_value": analytics.get('sales_pipeline', {}).get('total_pipeline_value', 0)
            },
            "full_analytics_data": analytics # On garde les données complètes si l'IA veut creuser
        }
        
        return context

    def _build_master_prompt(self, message: str, context: Dict, history: List[Dict]) -> Dict:
        """
        Assemble le prompt final en structurant tout le contexte collecté.
        """
        system_prompt = """
        Tu es un expert analyste de la collection privée BONVIN. Tu disposes d'une intelligence de raisonnement supérieure (GPT-4.1).
        Ton rôle n'est pas de suivre des instructions rigides, mais de raisonner à partir des différentes sources d'information qu'on te fournit.
        - Tu dois synthétiser les informations de la recherche sémantique, des analyses statistiques et de l'historique pour formuler la réponse la plus pertinente.
        - Fais preuve d'initiative. Si la recherche sémantique est plus pertinente, base-toi dessus. Si la question est d'ordre statistique, utilise l'analyse. Si c'est un mélange, fusionne les deux.
        - Adopte un ton direct, professionnel et extrêmement compétent. Tu es un conseiller, pas un simple robot.
        - Si les données te permettent d'identifier une opportunité ou un risque, mets-le en avant.
        """

        user_prompt = f"""
        **Historique de la conversation :**
        {json.dumps(history[-3:], indent=2) if history else "Aucune conversation en cours."}

        ---
        **Question actuelle de l'utilisateur :**
        "{message}"
        ---

        **CONTEXTE FOURNI POUR TON ANALYSE :**

        **1. Résultats de la Recherche Sémantique (les objets les plus proches du sens de la question) :**
        ```json
        {json.dumps(context['semantic_search'], indent=2)}
        ```

        **2. Résumé des Analyses Statistiques Globales :**
        ```json
        {json.dumps(context['analytics_summary'], indent=2)}
        ```

        **MISSION :**
        En te basant sur **toutes** ces informations, et en utilisant ton intelligence supérieure, formule la meilleure réponse possible à la question de l'utilisateur. Ne te contente pas de répéter les données, **interprète-les**.
        """

        return {
            "system": system_prompt,
            "user": user_prompt
        }

    def _query_ai_model(self, prompt_data: Dict) -> str:
        """Interroge le modèle IA avec le prompt construit."""
        if not self.ai_engine:
            return "Moteur IA indisponible."
        
        try:
            response = self.ai_engine.client.chat.completions.create(
                model="gpt-4o", # Mettez ici le nom exact du modèle si différent, ex: gpt-4.1-turbo
                messages=[
                    {"role": "system", "content": prompt_data["system"]},
                    {"role": "user", "content": prompt_data["user"]}
                ],
                temperature=0.4, # Un peu plus de liberté pour un raisonnement plus créatif
                max_tokens=1024
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Erreur lors de l'appel au modèle IA: {e}", exc_info=True)
            return "Je rencontre un problème pour contacter le service d'analyse. Veuillez réessayer."
