# enhanced_chatbot.py - Système de chatbot intelligent pour app.py

from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime, timedelta
import json

class EnhancedChatbot:
    """Chatbot intelligent avec analyse contextuelle avancée"""
    
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
        if intent_data['entities']['categories']:
            items = [item for item in items 
                    if item.category and item.category.lower() in 
                    [cat.lower() for cat in intent_data['entities']['categories']]]
        
        # Filtrer par statuts si spécifiés
        if intent_data['entities']['statuses']:
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
        if 'sales_tracking' in intent_data['intents']:
            context['sales_analysis'] = self.analyze_sales_progress(items)
        
        # Analyse de valuation
        if 'valuation' in intent_data['intents']:
            context['valuation_insights'] = self.get_valuation_insights(items)
        
        # Recherche intelligente
        if 'search' in intent_data['intents'] and intent_data['entities']['attributes']:
            context['filtered_items'] = self.smart_search(items, intent_data['entities']['attributes'])
        
        return context
    
    def analyze_sales_progress(self, items: List) -> Dict:
        """Analyse détaillée de la progression des ventes"""
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
            
            # Items "chauds" (avec activité récente)
            if item.last_action_date:
                last_action = datetime.fromisoformat(item.last_action_date)
                if (datetime.now() - last_action).days < 7:
                    analysis['hot_items'].append({
                        'name': item.name,
                        'status': item.sale_status,
                        'offer': item.current_offer
                    })
                elif (datetime.now() - last_action).days > 30:
                    analysis['stale_items'].append({
                        'name': item.name,
                        'days_inactive': (datetime.now() - last_action).days
                    })
        
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
            if data['total'] > 0:
                data['avg_asking'] = data['total_asking'] / (data['total'] - data['sold']) if data['total'] > data['sold'] else 0
            if data['sold'] > 0:
                data['avg_sold'] = data['total_sold'] / data['sold']
        
        insights['category_performance'] = categories
        
        # Analyse ROI
        for item in items:
            if item.acquisition_price and item.sold_price:
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
        
        # Créer un prompt enrichi selon l'intention
        if 'sales_tracking' in intent_data['intents']:
            return self.generate_sales_response(context, intent_data)
        elif 'statistics' in intent_data['intents']:
            return self.generate_statistics_response(context, intent_data)
        elif 'valuation' in intent_data['intents']:
            return self.generate_valuation_response(context, intent_data)
        elif 'recommendation' in intent_data['intents']:
            return self.generate_recommendation_response(context, intent_data)
        else:
            return self.generate_general_response(context, intent_data)
    
    def generate_sales_response(self, context: Dict, intent_data: Dict) -> str:
        """Génère une réponse détaillée sur les ventes"""
        if 'sales_analysis' not in context:
            return "Je n'ai pas trouvé d'informations sur les ventes."
        
        analysis = context['sales_analysis']
        
        response = f"""**📊 Analyse complète de vos ventes**

**Vue d'ensemble:**
• {analysis['total_for_sale']} objets actuellement en vente
• {analysis['with_offers']} ont reçu des offres (valeur totale: {self.format_price(analysis['total_offers_value'])})

**Progression par étape:**
"""
        
        status_labels = {
            'initial': '🏁 Initial',
            'presentation': '📋 Présentation',
            'intermediary': '🤝 Intermédiaires',
            'inquiries': '📞 Demandes',
            'viewing': '👁️ Visites',
            'negotiation': '💬 Négociation',
            'offer_received': '💰 Offre reçue',
            'offer_accepted': '✅ Offre acceptée',
            'paperwork': '📄 Formalités',
            'completed': '🎯 Finalisé'
        }
        
        for status, count in analysis['by_status'].items():
            label = status_labels.get(status, status)
            response += f"• {label}: {count} objet(s)\n"
        
        if analysis['hot_items']:
            response += "\n**🔥 Objets avec activité récente:**\n"
            for item in analysis['hot_items'][:5]:
                offer_text = f" - Offre: {self.format_price(item['offer'])}" if item['offer'] else ""
                response += f"• {item['name']} ({item['status']}){offer_text}\n"
        
        if analysis['stale_items']:
            response += "\n**⚠️ Objets nécessitant attention:**\n"
            for item in analysis['stale_items'][:3]:
                response += f"• {item['name']} - Inactif depuis {item['days_inactive']} jours\n"
        
        # Recommandations intelligentes
        response += "\n**💡 Recommandations IA:**\n"
        if analysis['stale_items']:
            response += "• Envisagez de revoir les prix ou la présentation des objets inactifs\n"
        if analysis['with_offers'] > analysis['total_for_sale'] * 0.3:
            response += "• Bon taux d'engagement! Concentrez-vous sur la conversion des offres\n"
        else:
            response += "• Augmentez la visibilité de vos annonces pour générer plus d'offres\n"
        
        return response
    
    def generate_statistics_response(self, context: Dict, intent_data: Dict) -> str:
        """Génère une réponse statistique détaillée"""
        
        # Filtrer selon les entités détectées
        filter_text = ""
        if intent_data['entities']['categories']:
            filter_text = f" pour {', '.join(intent_data['entities']['categories'])}"
        
        response = f"""**📈 Statistiques détaillées{filter_text}**

**Inventaire:**
• Total d'objets: {context['total_items']}
• Valeur totale disponible: {self.format_price(context['total_value'])}
• Objets en vente: {len(context['items_for_sale'])}

**Performance des ventes:**
• Ventes récentes: {len(context['recent_sales'])}
"""
        
        if 'valuation_insights' in context:
            insights = context['valuation_insights']
            
            response += "\n**Performance par catégorie:**\n"
            for cat, data in insights['category_performance'].items():
                if data['total'] > 0:
                    response += f"\n*{cat}:*\n"
                    response += f"• Total: {data['total']} objets\n"
                    if data['avg_asking'] > 0:
                        response += f"• Prix moyen demandé: {self.format_price(data['avg_asking'])}\n"
                    if data['sold'] > 0:
                        response += f"• Vendus: {data['sold']} (Prix moyen: {self.format_price(data['avg_sold'])})\n"
            
            if insights['roi_analysis']:
                response += "\n**🏆 Top 3 ROI:**\n"
                for item in insights['roi_analysis'][:3]:
                    response += f"• {item['name']}: +{item['roi_percentage']}% ({self.format_price(item['profit'])} de profit)\n"
        
        return response
    
    def generate_valuation_response(self, context: Dict, intent_data: Dict) -> str:
        """Génère une réponse sur la valuation"""
        if 'valuation_insights' not in context:
            return "Je n'ai pas assez de données pour une analyse de valuation."
        
        insights = context['valuation_insights']
        
        response = """**💎 Analyse de valuation intelligente**

**Aperçu du marché:**
"""
        
        # Catégories les plus valorisées
        top_categories = sorted(
            [(cat, data['avg_asking']) for cat, data in insights['category_performance'].items() 
             if data['avg_asking'] > 0],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        if top_categories:
            response += "\n**Catégories les plus valorisées:**\n"
            for cat, avg in top_categories:
                response += f"• {cat}: {self.format_price(avg)} en moyenne\n"
        
        # Analyse des tendances
        response += "\n**Tendances observées:**\n"
        
        # Calculer le taux de vente moyen
        total_items = sum(data['total'] for data in insights['category_performance'].values())
        total_sold = sum(data['sold'] for data in insights['category_performance'].values())
        if total_items > 0:
            sell_rate = (total_sold / total_items) * 100
            response += f"• Taux de vente global: {sell_rate:.1f}%\n"
        
        # ROI moyen
        if insights['roi_analysis']:
            avg_roi = sum(item['roi_percentage'] for item in insights['roi_analysis']) / len(insights['roi_analysis'])
            response += f"• ROI moyen sur les ventes: {avg_roi:.1f}%\n"
        
        return response
    
    def generate_recommendation_response(self, context: Dict, intent_data: Dict) -> str:
        """Génère des recommandations stratégiques"""
        response = """**🎯 Recommandations stratégiques personnalisées**

Basé sur l'analyse de votre collection, voici mes recommandations:

"""
        
        # Analyser les items en vente
        if context['items_for_sale']:
            avg_time_for_sale = 30  # Estimation
            if avg_time_for_sale > 60:
                response += "**Optimisation des ventes:**\n"
                response += "• ⚡ Vos objets restent longtemps en vente. Considérez:\n"
                response += "  - Réviser les prix (-5 à -10%)\n"
                response += "  - Améliorer les descriptions\n"
                response += "  - Utiliser plus de canaux de vente\n\n"
        
        # Recommandations par catégorie
        if 'valuation_insights' in context:
            insights = context['valuation_insights']
            
            # Identifier les catégories performantes
            high_roi_categories = []
            for cat, data in insights['category_performance'].items():
                if data['sold'] > 0 and data['avg_sold'] > data['avg_asking'] * 0.8:
                    high_roi_categories.append(cat)
            
            if high_roi_categories:
                response += "**Catégories performantes:**\n"
                response += f"• Focus sur: {', '.join(high_roi_categories)}\n"
                response += "• Ces catégories montrent une forte demande\n\n"
        
        # Timing
        response += "**Timing optimal:**\n"
        current_month = datetime.now().month
        if current_month in [11, 12, 1]:
            response += "• 🎄 Période idéale pour les montres et bijoux de luxe\n"
        elif current_month in [3, 4, 5]:
            response += "• 🌸 Bon moment pour les voitures et bateaux\n"
        
        return response
    
    def generate_general_response(self, context: Dict, intent_data: Dict) -> str:
        """Réponse générale enrichie"""
        response = f"""Je comprends votre question : "{intent_data['original_message']}"

Voici ce que je peux vous dire sur votre collection:

• Vous avez {context['total_items']} objets au total
• Valeur totale disponible: {self.format_price(context['total_value'])}
• {len(context['items_for_sale'])} objets sont actuellement en vente

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
        """Point d'entrée principal du chatbot"""
        try:
            # 1. Analyser l'intention
            intent_data = self.analyze_intent(message)
            
            # 2. Récupérer le contexte
            context = self.get_contextual_data(intent_data)
            
            # 3. Générer la réponse
            response = self.generate_intelligent_response(intent_data, context)
            
            # 4. Si on utilise l'IA pour enrichir
            if self.ai_engine and hasattr(self.ai_engine, 'complete'):
                enhanced_prompt = f"""
                Tu es l'assistant expert de la collection Bonvin. 
                
                Question de l'utilisateur: {message}
                
                Analyse préparée:
                {response}
                
                Contexte additionnel:
                - Historique de conversation: {history[-3:] if history else 'Nouvelle conversation'}
                
                Enrichis cette réponse en gardant le même niveau de détail et de professionnalisme.
                Ajoute des insights pertinents si possible. Utilise des emojis pour la clarté.
                Garde un ton professionnel mais accessible.
                """
                
                try:
                    ai_response = self.ai_engine.complete(enhanced_prompt)
                    return ai_response
                except:
                    # Fallback si l'IA échoue
                    return response
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur chatbot: {e}")
            return "Désolé, j'ai rencontré une erreur. Pouvez-vous reformuler votre question?"


# Intégration dans votre app.py
# Remplacez votre route chatbot existante par :

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """Endpoint du chatbot intelligent"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        history = data.get('history', [])
        
        # Initialiser le chatbot amélioré
        enhanced_bot = EnhancedChatbot(
            data_manager=AdvancedDataManager,
            ai_engine=ai_engine
        )
        
        # Traiter le message
        response = enhanced_bot.process_message(message, history)
        
        return jsonify({
            'reply': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur chatbot: {e}")
        return jsonify({
            'error': 'Erreur lors du traitement',
            'reply': 'Désolé, je ne peux pas traiter votre demande pour le moment.'
        }), 500
