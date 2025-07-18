# enhanced_chatbot.py - Version 3.0 avec raisonnement en plusieurs étapes et connaissance du domaine

import re
import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class EnhancedChatbot:
    """
    Chatbot V3 : combine une connaissance du domaine codée (filtrage) avec
    le raisonnement avancé de l'IA (synthèse) pour des réponses précises et pertinentes.
    """

    def __init__(self, data_manager, ai_engine):
        self.data_manager = data_manager
        self.ai_engine = ai_engine
        # CONNAISSANCE SPÉCIFIQUE AU DOMAINE
        self.domain_knowledge = {
            'voitures': {
                'marques': {
                    'italiennes': ['ferrari', 'lamborghini', 'maserati', 'alfa romeo', 'pagani'],
                    'allemandes': ['porsche', 'bmw', 'mercedes', 'audi'],
                    'anglaises': ['rolls', 'bentley', 'aston martin', 'mclaren', 'jaguar'],
                    'françaises': ['bugatti', 'peugeot', 'citroën', 'renault']
                }
            }
        }

    def process_message(self, message: str, history: List[Dict] = None) -> str:
        """
        Orchestre le flux de traitement :
        1. Comprendre l'intention et les entités (Qu'est-ce que l'utilisateur veut ?)
        2. Récupérer et filtrer les données pertinentes (Aller chercher la bonne information)
        3. Générer une réponse synthétique et intelligente (Présenter l'information)
        """
        history = history or []
        try:
            # Étape 1: Analyse de la requête
            parsed_query = self._parse_query(message)

            # Étape 2: Récupération des données
            context_data = self._retrieve_context_data(parsed_query)
            
            # Si aucune donnée n'est trouvée, retourner une réponse claire
            if not context_data.get("items"):
                return "Je n'ai trouvé aucun objet correspondant à votre demande. Pourriez-vous essayer de reformuler ?"

            # Étape 3: Génération de la réponse
            return self._generate_ai_response(parsed_query, context_data, history)

        except Exception as e:
            logger.error(f"Erreur critique dans le traitement du chatbot pour le message: '{message}'", exc_info=True)
            return "Désolé, une erreur technique m'empêche de traiter votre demande. L'équipe a été notifiée."

    def _parse_query(self, message: str) -> Dict:
        """Décompose la question de l'utilisateur en intention et entités spécifiques."""
        message_lower = message.lower()
        query_info = {'original_message': message, 'intent': 'unknown', 'filters': {}}

        # Détection d'intention simple
        if any(word in message_lower for word in ['combien', 'nombre']):
            query_info['intent'] = 'count'
        elif any(word in message_lower for word in ['liste', 'montre', 'quels sont']):
            query_info['intent'] = 'list'
        
        # Détection d'entités (catégorie, attributs)
        if 'voiture' in message_lower:
            query_info['filters']['category'] = 'Voitures'
            # Recherche d'attributs spécifiques aux voitures
            for origin, brands in self.domain_knowledge['voitures']['marques'].items():
                if origin in message_lower:
                    query_info['filters']['brand_origin'] = origin
                    query_info['filters']['brands'] = brands
                    break
        
        # ... ajouter d'autres détections d'entités ici (ex: "en vente", "vendus")
        if 'en vente' in message_lower:
            query_info['filters']['for_sale'] = True
        if 'vendus' in message_lower:
            query_info['filters']['status'] = 'Sold'

        return query_info

    def _retrieve_context_data(self, parsed_query: Dict) -> Dict:
        """Filtre la base de données pour ne récupérer que les objets pertinents."""
        all_items = self.data_manager.fetch_all_items()
        filtered_items = []

        # Application des filtres
        category = parsed_query['filters'].get('category')
        brands = parsed_query['filters'].get('brands')
        
        # Cas spécifique pour la question de l'utilisateur
        if category == 'Voitures' and brands:
            for item in all_items:
                if item.category == 'Voitures':
                    item_name_lower = item.name.lower()
                    if any(brand in item_name_lower for brand in brands):
                        filtered_items.append(item)
        else:
            # Logique de filtrage plus générale (à développer si besoin)
            # Pour l'instant, on retourne tous les items si pas de filtre clair
            filtered_items = all_items 

        # Formattage des données pour l'IA
        context = {
            "query_summary": f"Filtres appliqués : {json.dumps(parsed_query['filters'])}",
            "item_count": len(filtered_items),
            "items": [item.to_dict() for item in filtered_items]
        }
        return context

    def _generate_ai_response(self, parsed_query: Dict, context: Dict, history: List[Dict]) -> str:
        """Utilise GPT-4.1 pour générer une réponse naturelle à partir des données filtrées."""
        if not self.ai_engine:
            return "Moteur IA indisponible."

        system_prompt = """
        Tu es l'assistant expert de la collection BONVIN. Tu réponds de manière concise et directe.
        - Ta mission est de synthétiser les données PRÉ-FILTRÉES que l'on te fournit.
        - Si on te demande de compter, compte les objets dans la liste et donne le total.
        - Si on te demande une liste, liste les noms des objets.
        - Base ta réponse UNIQUEMENT sur les données fournies dans le contexte. N'invente rien.
        - Termine par une phrase courte et utile, ou une question de suivi pertinente.
        """

        user_prompt = f"""
        La question de l'utilisateur était : "{parsed_query['original_message']}"
        
        J'ai déjà filtré la base de données pour toi. Voici les données pertinentes :
        - Nombre d'objets trouvés : {context['item_count']}
        - Liste des objets (format JSON) :
        {json.dumps(context['items'][:10], indent=2)} 
        
        Instructions :
        1. Analyse la question originale de l'utilisateur et les données ci-dessus.
        2. Formule une réponse claire et directe.
        """

        try:
            response = self.ai_engine.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Erreur lors de l'appel au modèle IA: {e}", exc_info=True)
            return "Je rencontre un problème pour formuler ma réponse."
