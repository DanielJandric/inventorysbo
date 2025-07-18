# enhanced_chatbot.py - Version 5.0 (Finale) : Raisonnement Stratégique

import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class EnhancedChatbot:
    """
    Chatbot V5 : combine une connaissance du domaine pour un filtrage de données précis
    avec un raisonnement IA sur un contexte ciblé. L'objectif est la pertinence et la fiabilité.
    """

    def __init__(self, data_manager, ai_engine):
        self.data_manager = data_manager
        self.ai_engine = ai_engine
        # Connaissance spécifique au domaine pour un filtrage intelligent
        self.domain_knowledge = {
            'voitures': {
                'marques': {
                    'italiennes': ['ferrari', 'lamborghini', 'maserati', 'alfa romeo', 'pagani'],
                    'allemandes': ['porsche', 'bmw', 'mercedes', 'audi', 'vw', 'volkswagen'],
                    'anglaises': ['rolls', 'bentley', 'aston martin', 'mclaren', 'jaguar'],
                    'françaises': ['bugatti', 'peugeot', 'citroën', 'renault']
                }
            }
            # ... on peut ajouter ici d'autres connaissances (ex: types de montres)
        }

    def process_message(self, message: str, history: List[Dict] = None) -> str:
        """
        Orchestre le flux de traitement en 3 étapes :
        1. Analyse de la requête pour comprendre l'intention et les entités.
        2. Récupération stratégique des données : ne chercher QUE ce qui est nécessaire.
        3. Génération de la réponse par l'IA sur ce contexte précis.
        """
        history = history or []
        try:
            # Étape 1: Analyse de la requête
            parsed_query = self._parse_query(message)

            # Étape 2: Récupération des données
            context_data = self._retrieve_strategic_context(parsed_query)
            
            # Gérer le cas où aucune donnée pertinente n'est trouvée
            if not context_data.get("items"):
                return "Je n'ai trouvé aucun objet correspondant aux critères de votre demande. Essayez de reformuler."

            # Étape 3: Génération de la réponse
            return self._generate_ai_response(parsed_query, context_data, history)

        except Exception as e:
            logger.error(f"Erreur critique dans le traitement du chatbot pour le message: '{message}'", exc_info=True)
            return "Désolé, une erreur technique m'empêche de traiter votre demande. L'équipe a été notifiée."

    def _parse_query(self, message: str) -> Dict:
        """Décompose la question de l'utilisateur en une intention et des filtres précis."""
        message_lower = message.lower()
        query_info = {'original_message': message, 'intent': 'list', 'filters': {}} # 'list' par défaut

        # Détection d'intention
        if any(word in message_lower for word in ['combien', 'nombre de']):
            query_info['intent'] = 'count'
        
        # Détection d'entités (les filtres)
        if 'voiture' in message_lower:
            query_info['filters']['category'] = 'Voitures'
            # Utilisation de la connaissance du domaine
            for origin, brands in self.domain_knowledge['voitures']['marques'].items():
                if origin in message_lower or any(brand in message_lower for brand in brands):
                    query_info['filters']['brand_origin'] = origin
                    query_info['filters']['brands'] = brands
                    break
        
        if 'en vente' in message_lower:
            query_info['filters']['for_sale'] = True
        if 'négociation' in message_lower:
            query_info['filters']['sale_status'] = 'negotiation'
        if 'vendu' in message_lower:
            query_info['filters']['status'] = 'Sold'

        return query_info

    def _retrieve_strategic_context(self, parsed_query: Dict) -> Dict:
        """Filtre la base de données pour ne récupérer que les objets strictement nécessaires."""
        all_items = self.data_manager.fetch_all_items()
        
        # On commence avec tous les objets et on applique les filtres successivement
        filtered_items = all_items
        
        # Filtre par catégorie
        if 'category' in parsed_query['filters']:
            filtered_items = [item for item in filtered_items if item.category == parsed_query['filters']['category']]
        
        # Filtre par marques de voiture
        if 'brands' in parsed_query['filters']:
            brands_to_check = parsed_query['filters']['brands']
            filtered_items = [item for item in filtered_items if any(brand in item.name.lower() for brand in brands_to_check)]
            
        # Filtre par statut "en vente"
        if parsed_query['filters'].get('for_sale') is True:
            filtered_items = [item for item in filtered_items if item.for_sale is True]
            
        # Filtre par statut de vente (ex: négociation)
        if 'sale_status' in parsed_query['filters']:
            status_to_check = parsed_query['filters']['sale_status']
            filtered_items = [item for item in filtered_items if item.sale_status == status_to_check]

        # Filtre par statut général (ex: vendu)
        if 'status' in parsed_query['filters']:
            status_to_check = parsed_query['filters']['status']
            filtered_items = [item for item in filtered_items if item.status == status_to_check]

        # Formattage du contexte pour l'IA
        context = {
            "query_intent": parsed_query['intent'],
            "item_count": len(filtered_items),
            # On envoie une version concise des objets pour limiter la taille du prompt
            "items": [
                {"name": item.name, "year": item.construction_year, "price": item.asking_price or item.sold_price}
                for item in filtered_items
            ]
        }
        return context

    def _generate_ai_response(self, parsed_query: Dict, context: Dict, history: List[Dict]) -> str:
        """Utilise GPT-4.1 pour générer une réponse naturelle à partir du contexte CIBLÉ."""
        if not self.ai_engine:
            return "Moteur IA indisponible."

        system_prompt = """
        Tu es l'assistant expert de la collection BONVIN. Tu es un analyste brillant qui répond de manière directe, précise et professionnelle.
        Ta mission est de répondre à la question de l'utilisateur en te basant STRICTEMENT sur les données pré-filtrées que l'on te fournit.
        - Si l'intention est "count", compte les objets et donne le nombre total.
        - Si l'intention est "list", liste les noms des objets pertinents.
        - Formule la réponse de manière naturelle et termine par une phrase utile. N'ajoute pas de fioritures inutiles.
        """

        user_prompt = f"""
        **Question de l'utilisateur :** "{parsed_query['original_message']}"

        **Données pertinentes que j'ai extraites pour toi :**
        ```json
        {json.dumps(context, indent=2)}
        ```

        **Ta mission :**
        En te basant sur l'intention de la requête et les données ci-dessus, formule la réponse la plus claire et directe possible.
        """

        try:
            response = self.ai_engine.client.chat.completions.create(
                model="gpt-4o", # Assurez-vous que c'est le bon identifiant pour GPT-4.1
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1, # On vise la précision, pas la créativité
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Erreur lors de l'appel au modèle IA: {e}", exc_info=True)
            return "Je rencontre un problème pour contacter le service d'analyse. Veuillez réessayer."
