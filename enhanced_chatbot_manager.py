"""
Enhanced Chatbot Manager avec capacités avancées
Author: BONVIN AI Assistant
Version: 2.0
Date: 2025
"""

import os
import json
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class EnhancedChatbotManager:
    """
    Gestionnaire de chatbot amélioré avec :
    - Analyse prédictive
    - Recommandations intelligentes
    - Cache multi-niveaux
    - Traitement parallèle
    - Export de rapports
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.analytics_cache = {}
        self.response_templates = self._load_response_templates()
        
    def _load_response_templates(self) -> Dict[str, str]:
        """Charge les templates de réponses optimisés"""
        return {
            "greeting": "👋 Bonjour ! Je suis votre assistant IA BONVIN. Comment puis-je vous aider avec votre collection aujourd'hui ?",
            "analysis_intro": "📊 **Analyse approfondie de votre collection**\n\n",
            "recommendation": "💡 **Recommandation personnalisée**\n\n",
            "alert": "⚠️ **Point d'attention**\n\n",
            "success": "✅ **Action réalisée avec succès**\n\n",
            "thinking": "🤔 Je réfléchis à votre demande...",
            "export_ready": "📥 **Export prêt**\n\n"
        }
    
    def analyze_user_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyse avancée de l'intention utilisateur avec NLP
        """
        query_lower = query.lower()
        
        # Détection d'intentions multiples
        intents = {
            "analysis": False,
            "creation": False,
            "modification": False,
            "deletion": False,
            "export": False,
            "prediction": False,
            "recommendation": False,
            "comparison": False,
            "alert": False,
            "help": False
        }
        
        # Patterns de détection
        analysis_patterns = [
            r"analys", r"statistic", r"rapport", r"état", r"situation",
            r"performance", r"évolution", r"tendance", r"bilan"
        ]
        
        creation_patterns = [
            r"ajout", r"créer", r"nouveau", r"acheter", r"acqui",
            r"enregistr", r"insér"
        ]
        
        export_patterns = [
            r"export", r"télécharg", r"pdf", r"excel", r"csv",
            r"rapport", r"document", r"fichier"
        ]
        
        prediction_patterns = [
            r"prédi", r"prévoir", r"futur", r"projet", r"estim",
            r"anticip", r"probable", r"devrait"
        ]
        
        recommendation_patterns = [
            r"recommand", r"conseil", r"suggest", r"propos",
            r"devrais", r"optimal", r"meilleur", r"stratég"
        ]
        
        # Analyse des patterns
        for pattern in analysis_patterns:
            if re.search(pattern, query_lower):
                intents["analysis"] = True
                break
                
        for pattern in creation_patterns:
            if re.search(pattern, query_lower):
                intents["creation"] = True
                break
                
        for pattern in export_patterns:
            if re.search(pattern, query_lower):
                intents["export"] = True
                break
                
        for pattern in prediction_patterns:
            if re.search(pattern, query_lower):
                intents["prediction"] = True
                break
                
        for pattern in recommendation_patterns:
            if re.search(pattern, query_lower):
                intents["recommendation"] = True
                break
        
        # Extraction d'entités
        entities = self._extract_entities(query)
        
        # Score de confiance
        confidence = self._calculate_confidence(intents, entities)
        
        return {
            "intents": intents,
            "entities": entities,
            "confidence": confidence,
            "original_query": query,
            "complexity": self._assess_complexity(query)
        }
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extraction d'entités nommées dans la requête"""
        entities = {
            "categories": [],
            "brands": [],
            "dates": [],
            "amounts": [],
            "statuses": [],
            "locations": []
        }
        
        # Catégories connues
        categories_map = {
            "voiture": "Voitures",
            "bateau": "Bateaux",
            "montre": "Montres",
            "action": "Actions",
            "immobilier": "Immobilier",
            "art": "Art",
            "bijou": "Bijoux",
            "vin": "Vins",
            "avion": "Avions"
        }
        
        # Marques connues
        brands = [
            "ferrari", "porsche", "mercedes", "bmw", "audi",
            "rolex", "patek", "omega", "cartier",
            "axopar", "sunseeker", "riva"
        ]
        
        query_lower = query.lower()
        
        # Détection des catégories
        for keyword, category in categories_map.items():
            if keyword in query_lower:
                entities["categories"].append(category)
        
        # Détection des marques
        for brand in brands:
            if brand in query_lower:
                entities["brands"].append(brand.capitalize())
        
        # Détection des montants (CHF, k, M)
        amount_pattern = r'\d+(?:\.\d+)?(?:\s*(?:k|K|m|M|chf|CHF|€|\$))?'
        amounts = re.findall(amount_pattern, query)
        entities["amounts"] = amounts
        
        # Détection des dates
        date_patterns = [
            r'\d{4}',  # Années
            r'\d{1,2}/\d{1,2}/\d{4}',  # Dates complètes
            r'(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)'
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, query_lower)
            entities["dates"].extend(dates)
        
        return entities
    
    def _calculate_confidence(self, intents: Dict, entities: Dict) -> float:
        """Calcule un score de confiance pour l'analyse"""
        score = 0.5  # Base
        
        # Ajout pour chaque intention détectée
        active_intents = sum(1 for v in intents.values() if v)
        score += active_intents * 0.1
        
        # Ajout pour les entités trouvées
        for entity_list in entities.values():
            if entity_list:
                score += 0.05 * len(entity_list)
        
        return min(score, 1.0)
    
    def _assess_complexity(self, query: str) -> str:
        """Évalue la complexité de la requête"""
        word_count = len(query.split())
        
        if word_count < 5:
            return "simple"
        elif word_count < 15:
            return "moderate"
        else:
            return "complex"
    
    def generate_smart_suggestions(self, context: Dict) -> List[str]:
        """
        Génère des suggestions intelligentes basées sur le contexte
        """
        suggestions = []
        
        # Analyse du contexte
        if context.get("last_category") == "Actions":
            suggestions.extend([
                "Analyser la performance du portefeuille",
                "Voir les dividendes attendus",
                "Comparer avec les indices de marché"
            ])
        
        if context.get("recent_sale"):
            suggestions.extend([
                "Voir le récapitulatif des ventes",
                "Calculer les plus-values réalisées",
                "Optimiser la fiscalité"
            ])
        
        if context.get("high_value_items"):
            suggestions.extend([
                "Analyser la concentration des risques",
                "Proposer une stratégie de diversification",
                "Estimer les coûts d'assurance"
            ])
        
        # Suggestions temporelles
        current_month = datetime.now().month
        if current_month == 12:
            suggestions.append("Préparer le bilan annuel")
        elif current_month == 1:
            suggestions.append("Définir les objectifs de l'année")
        
        # Suggestions basées sur les tendances
        if context.get("trending_up"):
            suggestions.append("Identifier les opportunités de vente")
        elif context.get("trending_down"):
            suggestions.append("Revoir la stratégie d'investissement")
        
        return suggestions[:5]  # Limiter à 5 suggestions
    
    def predict_future_value(self, item_data: Dict, months: int = 12) -> Dict[str, Any]:
        """
        Prédit la valeur future d'un item basé sur les tendances historiques
        """
        predictions = {
            "optimistic": 0,
            "realistic": 0,
            "pessimistic": 0,
            "confidence": 0,
            "factors": []
        }
        
        # Calcul basé sur la catégorie et les tendances
        category = item_data.get("category", "")
        current_value = item_data.get("current_value", 0)
        
        if not current_value:
            return predictions
        
        # Taux de croissance par catégorie (basé sur des moyennes historiques)
        growth_rates = {
            "Voitures": {"min": -0.05, "avg": 0.02, "max": 0.15},
            "Montres": {"min": -0.02, "avg": 0.05, "max": 0.20},
            "Art": {"min": -0.10, "avg": 0.08, "max": 0.30},
            "Actions": {"min": -0.20, "avg": 0.07, "max": 0.25},
            "Immobilier": {"min": -0.05, "avg": 0.03, "max": 0.10},
            "Bateaux": {"min": -0.10, "avg": -0.05, "max": 0.05}
        }
        
        rates = growth_rates.get(category, {"min": -0.05, "avg": 0.02, "max": 0.10})
        
        # Calcul des prédictions
        time_factor = months / 12.0
        predictions["pessimistic"] = current_value * (1 + rates["min"] * time_factor)
        predictions["realistic"] = current_value * (1 + rates["avg"] * time_factor)
        predictions["optimistic"] = current_value * (1 + rates["max"] * time_factor)
        
        # Facteurs influençant
        if category == "Voitures":
            predictions["factors"].extend([
                "Kilométrage et état",
                "Rareté du modèle",
                "Tendances du marché collection"
            ])
        elif category == "Actions":
            predictions["factors"].extend([
                "Performance de l'entreprise",
                "Conditions macro-économiques",
                "Volatilité du marché"
            ])
        
        # Score de confiance
        predictions["confidence"] = 0.7 if category in growth_rates else 0.4
        
        return predictions
    
    def generate_executive_summary(self, items: List, analytics: Dict) -> str:
        """
        Génère un résumé exécutif professionnel
        """
        summary = f"""
# 📊 RÉSUMÉ EXÉCUTIF - COLLECTION BONVIN
*Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*

## 🎯 Vue d'ensemble
- **Valeur totale du patrimoine** : {self._format_currency(analytics.get('total_value', 0))}
- **Nombre d'actifs** : {len(items)} objets
- **Valeur moyenne par actif** : {self._format_currency(analytics.get('average_value', 0))}

## 📈 Performance
- **Plus-value latente totale** : {self._format_currency(analytics.get('unrealized_gains', 0))}
- **ROI moyen** : {analytics.get('average_roi', 0):.1f}%
- **Taux de rotation** : {analytics.get('turnover_rate', 0):.1f}%

## 🏆 Top 3 des actifs les plus valorisés
"""
        
        # Ajouter le top 3
        top_items = sorted(items, key=lambda x: x.get('current_value', 0), reverse=True)[:3]
        for i, item in enumerate(top_items, 1):
            summary += f"{i}. **{item.get('name', 'N/A')}** - {self._format_currency(item.get('current_value', 0))}\n"
        
        summary += """

## 💡 Recommandations stratégiques
1. **Diversification** : Considérer l'équilibrage du portefeuille
2. **Optimisation fiscale** : Revoir les actifs avec plus-values importantes
3. **Gestion des risques** : Évaluer l'assurance des actifs de haute valeur

---
*Ce rapport est généré automatiquement par l'IA BONVIN*
"""
        return summary
    
    def _format_currency(self, amount: float) -> str:
        """Formate un montant en CHF avec séparateurs"""
        if amount >= 1_000_000:
            return f"{amount/1_000_000:.2f}M CHF"
        elif amount >= 1_000:
            return f"{amount/1_000:.1f}k CHF"
        else:
            return f"{amount:.0f} CHF"
    
    def export_to_json(self, data: Dict) -> str:
        """Export des données en JSON formaté"""
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    def export_to_csv_content(self, items: List) -> str:
        """Génère le contenu CSV pour export"""
        import csv
        import io
        
        output = io.StringIO()
        
        if not items:
            return ""
        
        # Déterminer les colonnes
        fieldnames = items[0].keys() if items else []
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)
        
        return output.getvalue()
    
    def generate_market_insights(self, market_data: Dict) -> str:
        """
        Génère des insights de marché intelligents
        """
        insights = "## 🌍 Insights de Marché\n\n"
        
        # Analyse des tendances
        if market_data.get("trend") == "bullish":
            insights += "📈 **Tendance haussière détectée**\n"
            insights += "Les indicateurs suggèrent une poursuite de la hausse à court terme.\n\n"
        elif market_data.get("trend") == "bearish":
            insights += "📉 **Tendance baissière en cours**\n"
            insights += "Prudence recommandée, envisager des positions défensives.\n\n"
        
        # Volatilité
        volatility = market_data.get("volatility", "moderate")
        if volatility == "high":
            insights += "⚠️ **Volatilité élevée**\n"
            insights += "Les mouvements de prix sont importants, ajuster la gestion des risques.\n\n"
        
        # Opportunités
        if market_data.get("opportunities"):
            insights += "💡 **Opportunités identifiées**\n"
            for opp in market_data["opportunities"][:3]:
                insights += f"• {opp}\n"
        
        return insights
    
    def calculate_portfolio_metrics(self, items: List) -> Dict[str, Any]:
        """
        Calcule des métriques avancées du portefeuille
        """
        metrics = {
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "max_drawdown": 0,
            "value_at_risk": 0,
            "beta": 0,
            "alpha": 0,
            "correlation_matrix": {},
            "efficient_frontier": []
        }
        
        # Calculs simplifiés pour démonstration
        values = [item.get("current_value", 0) for item in items if item.get("current_value")]
        
        if values:
            metrics["value_at_risk"] = np.percentile(values, 5)
            metrics["average_value"] = np.mean(values)
            metrics["std_deviation"] = np.std(values)
            
            # Sharpe Ratio simplifié
            if metrics["std_deviation"] > 0:
                risk_free_rate = 0.02  # 2% taux sans risque
                expected_return = 0.07  # 7% rendement attendu
                metrics["sharpe_ratio"] = (expected_return - risk_free_rate) / (metrics["std_deviation"] / metrics["average_value"])
        
        return metrics
    
    async def process_async_request(self, request: Dict) -> Dict:
        """
        Traite les requêtes de manière asynchrone pour améliorer les performances
        """
        tasks = []
        
        # Créer les tâches parallèles
        if request.get("need_analysis"):
            tasks.append(self._async_analysis(request))
        
        if request.get("need_prediction"):
            tasks.append(self._async_prediction(request))
        
        if request.get("need_recommendations"):
            tasks.append(self._async_recommendations(request))
        
        # Exécuter en parallèle
        results = await asyncio.gather(*tasks)
        
        # Combiner les résultats
        combined = {}
        for result in results:
            combined.update(result)
        
        return combined
    
    async def _async_analysis(self, request: Dict) -> Dict:
        """Analyse asynchrone"""
        await asyncio.sleep(0.1)  # Simulation
        return {"analysis": "Analyse complète..."}
    
    async def _async_prediction(self, request: Dict) -> Dict:
        """Prédiction asynchrone"""
        await asyncio.sleep(0.1)  # Simulation
        return {"prediction": "Prédictions calculées..."}
    
    async def _async_recommendations(self, request: Dict) -> Dict:
        """Recommandations asynchrones"""
        await asyncio.sleep(0.1)  # Simulation
        return {"recommendations": ["Rec 1", "Rec 2", "Rec 3"]}


class ConversationOptimizer:
    """
    Optimise les conversations pour une meilleure expérience utilisateur
    """
    
    def __init__(self):
        self.conversation_patterns = self._load_patterns()
        self.response_cache = {}
        
    def _load_patterns(self) -> Dict:
        """Charge les patterns de conversation"""
        return {
            "greetings": [
                "bonjour", "bonsoir", "salut", "hello", "hey"
            ],
            "thanks": [
                "merci", "thanks", "parfait", "super", "génial"
            ],
            "questions": [
                "comment", "pourquoi", "quand", "où", "combien", "quel"
            ],
            "actions": [
                "ajoute", "supprime", "modifie", "crée", "change"
            ]
        }
    
    def optimize_response(self, response: str, context: Dict) -> str:
        """
        Optimise la réponse en fonction du contexte
        """
        # Ajouter des émojis appropriés
        response = self._add_contextual_emojis(response, context)
        
        # Formater les nombres
        response = self._format_numbers(response)
        
        # Ajouter des liens d'action
        response = self._add_action_links(response, context)
        
        # Structurer avec Markdown
        response = self._enhance_markdown(response)
        
        return response
    
    def _add_contextual_emojis(self, text: str, context: Dict) -> str:
        """Ajoute des émojis contextuels"""
        emoji_map = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️",
            "money": "💰",
            "chart": "📊",
            "car": "🚗",
            "watch": "⌚",
            "boat": "🛥️",
            "house": "🏠",
            "art": "🎨"
        }
        
        # Logique d'ajout d'émojis basée sur le contexte
        if context.get("category") == "Voitures" and "🚗" not in text:
            text = "🚗 " + text
        
        return text
    
    def _format_numbers(self, text: str) -> str:
        """Formate les nombres pour une meilleure lisibilité"""
        # Regex pour trouver les nombres
        number_pattern = r'\b(\d{4,})\b'
        
        def format_number(match):
            num = int(match.group(1))
            if num >= 1_000_000:
                return f"{num/1_000_000:.1f}M"
            elif num >= 1_000:
                return f"{num/1_000:.0f}k"
            return str(num)
        
        return re.sub(number_pattern, format_number, text)
    
    def _add_action_links(self, text: str, context: Dict) -> str:
        """Ajoute des liens d'action cliquables"""
        # Cette fonction pourrait ajouter des boutons ou liens
        # selon le contexte de la conversation
        return text
    
    def _enhance_markdown(self, text: str) -> str:
        """Améliore le formatage Markdown"""
        # Assurer que les listes sont bien formatées
        text = re.sub(r'^- ', '• ', text, flags=re.MULTILINE)
        
        # Mettre en gras les points importants
        important_words = ["important", "attention", "crucial", "essentiel"]
        for word in important_words:
            text = re.sub(f'\\b{word}\\b', f'**{word}**', text, flags=re.IGNORECASE)
        
        return text
    
    def suggest_follow_up_questions(self, conversation: List[Dict]) -> List[str]:
        """
        Suggère des questions de suivi pertinentes
        """
        suggestions = []
        
        if not conversation:
            return [
                "Comment va ma collection ?",
                "Quelle est la valeur totale ?",
                "Quels sont mes objets les plus précieux ?"
            ]
        
        last_message = conversation[-1] if conversation else {}
        content = last_message.get("content", "").lower()
        
        # Suggestions basées sur le dernier message
        if "valeur" in content:
            suggestions.extend([
                "Comment a évolué la valeur sur 6 mois ?",
                "Quelle catégorie a le plus de valeur ?",
                "Comparer avec l'année dernière"
            ])
        
        if "vente" in content:
            suggestions.extend([
                "Quels objets recommandez-vous de vendre ?",
                "Quel est le meilleur moment pour vendre ?",
                "Calculer les plus-values potentielles"
            ])
        
        if "action" in content or "stock" in content:
            suggestions.extend([
                "Analyser la performance du portefeuille",
                "Comparer avec le S&P 500",
                "Voir les dividendes de l'année"
            ])
        
        return suggestions[:3]  # Retourner maximum 3 suggestions


# Instance globale pour usage facile
enhanced_chatbot = EnhancedChatbotManager()
conversation_optimizer = ConversationOptimizer()
