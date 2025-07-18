# enhanced_chatbot.py - Version 2.0 avec mémoire, IA proactive et recherche sémantique avancée

import re
import logging
from datetime import datetime
from typing import Dict, List, Any

# Initialiser le logger pour ce module
logger = logging.getLogger(__name__)

class EnhancedChatbot:
    """
    Chatbot intelligent V2 avec :
    - Mémoire conversationnelle pour le suivi de contexte.
    - Intégration profonde de la recherche sémantique (RAG).
    - Analyse d'intention et génération de réponses dynamiques via l'IA.
    - Suggestions proactives basées sur l'analyse des données.
    """
    
    def __init__(self, data_manager, ai_engine):
        self.data_manager = data_manager
        self.ai_engine = ai_engine
        # AMÉLIORATION: Ajout d'un cache simple pour la conversation
        self.conversation_cache = {}

    def process_message(self, message: str, history: List[Dict] = None) -> str:
        """
        Point d'entrée principal du chatbot. Orchestre l'analyse, la recherche et la génération de réponse.
        """
        history = history or []
        
        try:
            # 1. Analyse de l'intention et des entités
            intent_data = self._analyze_intent_and_entities(message, history)
            
            # 2. Récupération et enrichissement du contexte
            # Utilise la recherche sémantique si l'intention est appropriée
            if intent_data['primary_intent'] in ['search', 'technical', 'comparison']:
                context = self._get_semantic_context(intent_data)
            else:
                context = self._get_analytical_context(intent_data)

            # 3. Génération de la réponse via le moteur IA
            # Le moteur IA reçoit une instruction claire et des données structurées
            response = self._generate_ai_response(intent_data, context, history)
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur critique dans le traitement du chatbot pour le message: '{message}'", exc_info=True)
            return "Désolé, une erreur inattendue est survenue. L'équipe technique a été notifiée. Pourriez-vous reformuler votre demande ?"

    def _analyze_intent_and_entities(self, message: str, history: List[Dict]) -> Dict:
        """
        AMÉLIORATION: Utilise l'historique pour mieux comprendre l'intention.
        Détecte l'intention principale, les entités et si la question est une suite de la conversation.
        """
        message_lower = message.lower()
        
        patterns = {
            'search': [r'trouve', r'cherche', r'liste', r'montre', r'affiche', r'quels sont', r'y a-t-il'],
            'sales_tracking': [r'vente', r'négociation', r'offre', r'acheteur', r'pipeline', r'où en sont'],
            'statistics': [r'combien', r'nombre', r'total', r'statistique', r'stats', r'données'],
            'valuation': [r'valeur', r'estimation', r'vaut', r'prix', r'coûte'],
            'recommendation': [r'devrais-je', r'conseille', r'recommande', r'suggestion', r'stratégie'],
            'comparison': [r'compare', r'différence', r'versus', r'vs', r'lequel est le meilleur'],
            'technical': [r'caractéristiques', r'specs', r'détails techniques', r'moteur', r'puissance']
        }
        
        primary_intent = 'general'
        for intent, keywords in patterns.items():
            if any(re.search(pattern, message_lower) for pattern in keywords):
                primary_intent = intent
                break
        
        # CORRECTION ICI: Utilisation de guillemets doubles pour la chaîne contenant une apostrophe
        follow_up_keywords = ['et pour', 'peux-tu préciser', "dis-m'en plus", 'pourquoi', 'lesquels']
        is_follow_up = any(keyword in message_lower for keyword in follow_up_keywords) or (len(message.split()) <= 3)

        return {
            'original_message': message,
            'primary_intent': primary_intent,
            'is_follow_up': is_follow_up,
        }

    def _get_semantic_context(self, intent_data: Dict) -> Dict:
        """
        AMÉLIORATION: Utilise la recherche sémantique pour trouver les objets les plus pertinents.
        C'est le cœur du RAG (Retrieval-Augmented Generation).
        """
        query = intent_data['original_message']
        all_items = self.data_manager.fetch_all_items()
        
        if not self.ai_engine or not hasattr(self.ai_engine, 'semantic_search'):
            return {'error': "Le moteur de recherche sémantique n'est pas disponible."}
            
        search_results = self.ai_engine.semantic_search.semantic_search(query, all_items, top_k=10)
        
        relevant_items = []
        for item, score in search_results:
            if score > 0.6: 
                relevant_items.append({
                    'name': item.name,
                    'category': item.category,
                    'status': item.status,
                    'year': item.construction_year,
                    'price': item.asking_price or item.sold_price,
                    'description': item.description,
                    'relevance_score': score
                })

        return {
            'type': 'semantic_search',
            'query': query,
            'found_items': relevant_items,
            'summary': f"{len(relevant_items)} objets pertinents trouvés pour '{query}'."
        }

    def _get_analytical_context(self, intent_data: Dict) -> Dict:
        """
        Récupère des données agrégées pour les questions statistiques ou analytiques.
        """
        all_items = self.data_manager.fetch_all_items()
        analytics = self.data_manager.calculate_advanced_analytics(all_items)
        
        context = {
            'type': 'analytics',
            'query': intent_data['original_message'],
            'data': {}
        }
        
        intent = intent_data['primary_intent']
        if intent == 'sales_tracking':
            context['data'] = analytics.get('sales_pipeline')
            context['summary'] = "Analyse du pipeline de ventes."
        elif intent == 'statistics':
            context['data'] = {
                'basics': analytics.get('basic_metrics'),
                'financials': analytics.get('financial_metrics')
            }
            context['summary'] = "Statistiques générales et financières de la collection."
        elif intent == 'valuation':
             context['data'] = {
                'by_category': analytics.get('category_analytics'),
                'market_insights': analytics.get('market_insights')
            }
             context['summary'] = "Analyse de la valeur et des tendances du marché."
        else:
            context['data'] = analytics
            context['summary'] = "Vue d'ensemble complète de la collection."
            
        return context

    def _generate_ai_response(self, intent_data: Dict, context: Dict, history: List[Dict]) -> str:
        """
        AMÉLIORATION: Construit un prompt structuré pour le modèle IA (GPT-4) et génère une réponse naturelle.
        """
        if not self.ai_engine:
            return "Le moteur d'intelligence artificielle n'est pas configuré. Je ne peux pas générer de réponse."
            
        system_prompt = """
        Tu es l'assistant IA expert de la collection privée BONVIN. Tu es analytique, proactif et tu communiques de manière claire et professionnelle.
        - Ta mission est de transformer les données brutes fournies en une réponse naturelle, pertinente et utile.
        - Structure tes réponses avec des titres (en gras) et des listes à puces.
        - Sois proactif : si tu détectes une anomalie ou une opportunité dans les données, mentionne-la et propose une action.
        - Utilise l'historique de la conversation pour comprendre les questions de suivi.
        """
        
        user_prompt = f"""
        Historique de la conversation (les derniers échanges):
        {history[-3:] if history else "Aucun historique."}
        
        Question actuelle de l'utilisateur: "{intent_data['original_message']}"
        
        Voici les données que j'ai récupérées pour répondre à cette question :
        - Type de données : {context.get('type')}
        - Résumé des données : {context.get('summary')}
        - Données brutes (en format JSON) :
        {str(context.get('data') or context.get('found_items'))}
        
        Instructions pour ta réponse :
        1. Synthétise ces données pour répondre directement et précisément à la question de l'utilisateur.
        2. Ne te contente pas de lister les données, interprète-les ! Explique ce qu'elles signifient.
        3. Si les données révèlent une opportunité (ex: un objet très recherché) ou un risque (ex: un objet en vente depuis trop longtemps), signale-le.
        4. Termine ta réponse par une ou deux suggestions de questions de suivi pertinentes.
        """
        
        try:
            response = self.ai_engine.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Erreur lors de l'appel au modèle IA: {e}", exc_info=True)
            return "Je rencontre un problème pour formuler ma réponse. Veuillez réessayer."
