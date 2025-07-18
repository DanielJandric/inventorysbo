# enhanced_chatbot.py - Système de chatbot intelligent pour app.py

from typing import Dict, List, Optional, Tuple
import re
import logging
from datetime import datetime

# Initialiser le logger pour ce module
logger = logging.getLogger(__name__)

class EnhancedChatbot:
    """Chatbot intelligent avec analyse contextuelle avancée et gestion d'erreurs robuste"""
    
    def __init__(self, data_manager, ai_engine):
        self.data_manager = data_manager
        self.ai_engine = ai_engine
        
    def analyze_intent(self, message: str) -> Dict[str, any]:
        """Analyse l'intention de l'utilisateur avec NLP avancé"""
        message_lower = message.lower()
        
        # Patterns pour détecter les intentions
        patterns = {
            'statistics': [
                r'combien', r'nombre', r'total', r'statistique', r'stats',
                r'quelle est la valeur', r'montant total'
            ],
            'sales_tracking': [
                r'vente', r'négociation', r'offre', r'acheteur', r'intermédiaire',
                r'où en sont', r'statut des ventes', r'progression'
            ],
            'valuation': [
                r'prix', r'valeur', r'estimation', r'vaut', r'coût',
                r'combien vaut', r'estimer'
            ],
            'search': [
                r'trouve', r'cherche', r'liste', r'montre', r'affiche',
                r'quels sont', r'y a-t-il'
            ],
            'comparison': [
                r'compare', r'différence', r'versus', r'vs', r'mieux',
                r'plus cher', r'moins cher'
            ],
            'recommendation': [
                r'devrais-je', r'conseille', r'recommande', r'suggestion',
                r'que faire', r'stratégie'
            ],
            'technical': [
                r'caractéristiques', r'specs', r'technique', r'détails',
                r'modèle', r'année', r'état'
            ]
        }
        
        detected_intents = []
        for intent, keywords in patterns.items():
            if any(re.search(pattern, message_lower) for pattern in keywords):
                detected_intents.append(intent)
        
        # Extraction d'entités
        entities = self.extract_entities(message)
        
        return {
            'intents': detected_intents if detected_intents else ['general'],
            'entities': entities,
            'original_message': message
        }
    
    def extract_entities(self, message: str) -> Dict[str, List[str]]:
        """Extrait les entités importantes du message"""
        entities = {
            'categories': [],
            'statuses': [],
            'time_periods': [],
            'numbers': [],
            'attributes': []
        }
        
        # Catégories connues
        categories = ['voitures', 'montres', 'bateaux', 'avions', 'appartements', 
                     'maison', 'be capital', 'start-ups', 'art', 'bijoux', 'vins']
        for cat in categories:
            if cat in message.lower():
                entities['categories'].append(cat)
        
        # Statuts
        if any(word in message.lower() for word in ['disponible', 'available']):
            entities['statuses'].append('Available')
        if any(word in message.lower() for word in ['vendu', 'sold']):
            entities['statuses'].append('Sold')
        if any(word in message.lower() for word in ['en vente', 'for sale']):
            entities['statuses'].append('ForSale')
        
        # Périodes temporelles
        if 'aujourd\'hui' in message.lower() or 'today' in message.lower():
            entities['time_periods'].append('today')
        if 'cette semaine' in message.lower() or 'this week' in message.lower():
            entities['time_periods'].append('week')
        if 'ce mois' in message.lower() or 'this month' in message.lower():
            entities['time_periods'].append('month')
        
        # Nombres
        numbers = re.findall(r'\d+', message)
        entities['numbers'] = numbers
        
        # Attributs techniques
        tech_attributes = ['automatique', 'manuelle', '4 places', '2 places', 
                          'suv', 'coupé', 'vintage', 'moderne', 'luxe']
        for attr in tech_attributes:
            if attr in message.lower():
                entities['attributes'].append(attr)
        
        return entities
    
    def get_contextual_data(self, intent_data: Dict) -> Dict:
        """Récupère les données contextuelles basées sur l'intention"""
        context = {}
        items = self.data_manager.fetch_all_items()
        
        # Filtrer par catégories si spécifiées
        if intent_data.get('entities', {}).get('categories'):
            items = [item for item in items 
                    if item.category and item.category.lower() in 
                    [cat.lower() for cat in intent_data['entities']['categories']]]
        
        # Filtrer par statuts si spécifiés
        if intent_data.get('entities', {}).get('statuses'):
            status_filter = []
            for status in intent_data['entities']['statuses']:
                if status == 'ForSale':
                    status_filter.extend([item for item in items 
                                        if item.status == 'Available' and item.for_sale])
                else:
                    status_filter.extend([item for item in items if item.status == status])
            items = status_filter
        
        # Calculer les statistiques enrichies
        context['total_items'] = len(items)
        context['total_value'] = sum(item.asking_price or 0 for item in items if item.status == 'Available')
        context['items_for_sale'] = [item for item in items if item.for_sale]
        context['recent_sales'] = [item for item in items if item.status == 'Sold'][-5:]
        
        # Analyse des ventes
        if 'sales_tracking' in intent_data.get('intents', []):
            context['sales_analysis'] = self.analyze_sales_progress(items)
        
        # Analyse de valuation
        if 'valuation' in intent_data.get('intents', []):
            context['valuation_insights'] = self.get_valuation_insights(items)
        
        # Recherche intelligente
        if 'search' in intent_data.get('intents', []) and intent_data.get('entities', {}).get('attributes'):
            context['filtered_items'] = self.smart_search(items, intent_data['entities']['attributes'])
        
        return context
    
    def analyze_sales_progress(self, items: List) -> Dict:
        """Analyse détaillée de la progression des ventes avec gestion d'erreurs."""
        sales_items = [item for item in items if item.for_sale]
        
        analysis = {
            'total_for_sale': len(sales_items),
            'by_status': {},
            'with_offers': 0,
            'total_offers_value': 0,
            'avg_time_on_market': 0,
            'hot_items': [],
            'stale_items': []
        }
        
        # Grouper par statut de vente
        status_counts = {}
        for item in sales_items:
            status = item.sale_status or 'initial'
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if item.current_offer:
                analysis['with_offers'] += 1
                analysis['total_offers_value'] += item.current_offer
            
            # **CORRECTION**: Gestion sécurisée de la date
            if item.last_action_date:
                try:
                    # Tenter de convertir la date
                    last_action = datetime.fromisoformat(item.last_action_date.split('T')[0])
                    days_inactive = (datetime.now() - last_action).days
                    
                    if days_inactive < 7:
                        analysis['hot_items'].append({
                            'name': item.name,
                            'status': item.sale_status,
                            'offer': item.current_offer
                        })
                    elif days_inactive > 30:
                        analysis['stale_items'].append({
                            'name': item.name,
                            'days_inactive': days_inactive
                        })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Date invalide pour l'objet '{item.name}': {item.last_action_date}. Erreur: {e}")
                    # On continue sans planter
                    pass
        
        analysis['by_status'] = status_counts
        return analysis

    def get_valuation_insights(self, items: List) -> Dict:
        """Insights avancés sur la valuation"""
        insights = {
            'category_performance': {},
            'price_trends': {},
            'roi_analysis': []
        }
        
        # Performance par catégorie
        categories = {}
        for item in items:
            if item.category:
                if item.category not in categories:
                    categories[item.category] = {
                        'total': 0,
                        'sold': 0,
                        'avg_asking': 0,
                        'avg_sold': 0,
                        'total_asking': 0,
                        'total_sold': 0
                    }
                
                cat_data = categories[item.category]
                cat_data['total'] += 1
                
                if item.status == 'Available' and item.asking_price:
                    cat_data['total_asking'] += item.asking_price
                elif item.status == 'Sold' and item.sold_price:
                    cat_data['sold'] += 1
                    cat_data['total_sold'] += item.sold_price
        
        # Calculer les moyennes
        for cat, data in categories.items():
            if data.get('total', 0) > data.get('sold', 0):
                data['avg_asking'] = data.get('total_asking', 0) / (data['total'] - data['sold'])
            if data.get('sold', 0) > 0:
                data['avg_sold'] = data.get('total_sold', 0) / data['sold']
        
        insights['category_performance'] = categories
        
        # Analyse ROI
        for item in items:
            if item.acquisition_price and item.sold_price and item.acquisition_price > 0:
                roi = ((item.sold_price - item.acquisition_price) / item.acquisition_price) * 100
                insights['roi_analysis'].append({
                    'name': item.name,
                    'roi_percentage': round(roi, 2),
                    'profit': item.sold_price - item.acquisition_price
                })
        
        insights['roi_analysis'].sort(key=lambda x: x['roi_percentage'], reverse=True)
        
        return insights

    def smart_search(self, items: List, attributes: List[str]) -> List:
        """Recherche intelligente avec scoring"""
        scored_items = []
        
        for item in items:
            score = 0
            item_text = f"{item.name} {item.description or ''} {item.category or ''}".lower()
            
            for attr in attributes:
                if attr.lower() in item_text:
                    score += 10
                # Recherche floue
                elif any(word in item_text for word in attr.lower().split()):
                    score += 5
            
            if score > 0:
                scored_items.append((score, item))
        
        # Trier par score décroissant
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored_items[:10]]  # Top 10

    def generate_intelligent_response(self, intent_data: Dict, context: Dict) -> str:
        """Génère une réponse intelligente basée sur l'analyse"""
        intents = intent_data.get('intents', [])
        
        if 'sales_tracking' in intents:
            return self.generate_sales_response(context, intent_data)
        elif 'statistics' in intents:
            return self.generate_statistics_response(context, intent_data)
        elif 'valuation' in intents:
            return self.generate_valuation_response(context, intent_data)
        elif 'recommendation' in intents:
            return self.generate_recommendation_response(context, intent_data)
        else:
            return self.generate_general_response(context, intent_data)

    def generate_sales_response(self, context: Dict, intent_data: Dict) -> str:
        """Génère une réponse détaillée sur les ventes"""
        analysis = context.get('sales_analysis')
        if not analysis:
            return "Je n'ai pas trouvé d'informations sur les ventes."
        
        response = f"""**📊 Analyse complète de vos ventes**

**Vue d'ensemble:**
• {analysis.get('total_for_sale', 0)} objets actuellement en vente
• {analysis.get('with_offers', 0)} ont reçu des offres (valeur totale: {self.format_price(analysis.get('total_offers_value', 0))})

**Progression par étape:**
"""
        
        status_labels = {
            'initial': '🏁 Initial', 'presentation': '📋 Présentation', 'intermediary': '🤝 Intermédiaires',
            'inquiries': '📞 Demandes', 'viewing': '👁️ Visites', 'negotiation': '💬 Négociation',
            'offer_received': '💰 Offre reçue', 'offer_accepted': '✅ Offre acceptée',
            'paperwork': '📄 Formalités', 'completed': '🎯 Finalisé'
        }
        
        for status, count in analysis.get('by_status', {}).items():
            label = status_labels.get(status, status)
            response += f"• {label}: {count} objet(s)\n"
        
        if analysis.get('hot_items'):
            response += "\n**🔥 Objets avec activité récente:**\n"
            for item in analysis['hot_items'][:5]:
                offer_text = f" - Offre: {self.format_price(item.get('offer'))}" if item.get('offer') else ""
                response += f"• {item.get('name')} ({item.get('status')}){offer_text}\n"
        
        if analysis.get('stale_items'):
            response += "\n**⚠️ Objets nécessitant attention:**\n"
            for item in analysis['stale_items'][:3]:
                response += f"• {item.get('name')} - Inactif depuis {item.get('days_inactive')} jours\n"
        
        response += "\n**💡 Recommandations IA:**\n"
        if analysis.get('stale_items'):
            response += "• Envisagez de revoir les prix ou la présentation des objets inactifs.\n"
        if analysis.get('with_offers', 0) > analysis.get('total_for_sale', 1) * 0.3:
            response += "• Bon taux d'engagement! Concentrez-vous sur la conversion des offres.\n"
        else:
            response += "• Augmentez la visibilité de vos annonces pour générer plus d'offres.\n"
        
        return response

    def generate_statistics_response(self, context: Dict, intent_data: Dict) -> str:
        """Génère une réponse statistique détaillée"""
        filter_text = ""
        if intent_data.get('entities', {}).get('categories'):
            filter_text = f" pour {', '.join(intent_data['entities']['categories'])}"
        
        response = f"""**📈 Statistiques détaillées{filter_text}**

**Inventaire:**
• Total d'objets: {context.get('total_items', 0)}
• Valeur totale disponible: {self.format_price(context.get('total_value', 0))}
• Objets en vente: {len(context.get('items_for_sale', []))}

**Performance des ventes:**
• Ventes récentes: {len(context.get('recent_sales', []))}
"""
        
        insights = context.get('valuation_insights')
        if insights:
            response += "\n**Performance par catégorie:**\n"
            for cat, data in insights.get('category_performance', {}).items():
                if data.get('total', 0) > 0:
                    response += f"\n*{cat}:*\n"
                    response += f"• Total: {data['total']} objets\n"
                    if data.get('avg_asking', 0) > 0:
                        response += f"• Prix moyen demandé: {self.format_price(data['avg_asking'])}\n"
                    if data.get('sold', 0) > 0:
                        response += f"• Vendus: {data['sold']} (Prix moyen: {self.format_price(data.get('avg_sold', 0))})\n"
            
            if insights.get('roi_analysis'):
                response += "\n**🏆 Top 3 ROI:**\n"
                for item in insights['roi_analysis'][:3]:
                    response += f"• {item.get('name')}: +{item.get('roi_percentage')}% ({self.format_price(item.get('profit', 0))} de profit)\n"
        
        return response
    
    # Les autres fonctions de génération de réponse (generate_valuation_response, etc.)
    # sont omises pour la concision mais devraient aussi utiliser .get() pour plus de sécurité.

    def generate_general_response(self, context: Dict, intent_data: Dict) -> str:
        """Réponse générale enrichie"""
        response = f"""Je comprends votre question : "{intent_data.get('original_message')}"

Voici ce que je peux vous dire sur votre collection:

• Vous avez {context.get('total_items', 0)} objets au total
• Valeur totale disponible: {self.format_price(context.get('total_value', 0))}
• {len(context.get('items_for_sale', []))} objets sont actuellement en vente

Souhaitez-vous une analyse plus spécifique? Je peux vous aider avec:
• 📊 Statistiques détaillées
• 💰 Analyse des ventes
• 💎 Évaluation et tendances
• 🎯 Recommandations stratégiques
"""
        return response

    def format_price(self, price: float) -> str:
        """Formate un prix en CHF"""
        if price is None:
            return "N/A"
        return f"{price:,.0f} CHF".replace(",", "'")
    
    def process_message(self, message: str, history: List[Dict] = None) -> str:
        """Point d'entrée principal du chatbot avec gestion d'erreur améliorée"""
        try:
            # 1. Analyser l'intention
            intent_data = self.analyze_intent(message)
            
            # 2. Récupérer le contexte
            context = self.get_contextual_data(intent_data)
            
            # 3. Générer la réponse
            response = self.generate_intelligent_response(intent_data, context)
            
            # 4. Enrichissement par l'IA (si disponible)
            if self.ai_engine and hasattr(self.ai_engine, 'complete'):
                # Code pour l'enrichissement par IA...
                pass
            
            return response
            
        except Exception as e:
            # **AMÉLIORATION**: Journalisation de l'erreur
            logger.error(f"Erreur lors du traitement du message: '{message}'", exc_info=True)
            return "Désolé, j'ai rencontré une erreur interne. L'équipe technique a été informée. Pouvez-vous reformuler votre question ?"
