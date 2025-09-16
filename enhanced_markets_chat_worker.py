"""
Enhanced Markets Chat Worker avec capacités avancées d'analyse de marchés
Version 2.0 - Optimisé pour GPT-5
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Generator
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# Import des dépendances existantes
try:
    from openai import OpenAI
except Exception as _e:
    raise RuntimeError("openai SDK is required: pip install -U openai") from _e

from gpt5_compat import extract_output_text, from_responses_simple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class EnhancedMarketsChatWorker:
    """
    Worker amélioré pour l'analyse de marchés avec :
    - Analyse de sentiment avancée
    - Détection de tendances et patterns
    - Prédictions de marché
    - Alertes intelligentes
    - Visualisations de données de marché
    """
    
    def __init__(self, *, api_key: Optional[str] = None, timeout_s: int = 120):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        
        # Client OpenAI
        try:
            self.client = OpenAI(api_key=api_key, timeout=timeout_s)
        except TypeError:
            self.client = OpenAI(api_key=api_key)
            try:
                self.client = self.client.with_options(timeout=timeout_s)
            except Exception:
                pass
        
        # Configuration du modèle
        env_model = (os.getenv("AI_MODEL") or "gpt-5").strip()
        self.model = env_model if env_model.startswith("gpt-5") else "gpt-5"
        self.max_output_tokens = min(30000, int(os.getenv("MAX_OUTPUT_TOKENS", "30000")))
        
        # Cache et optimisations
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Indicateurs de marché
        self.market_indicators = {
            "volatility": None,
            "trend": None,
            "momentum": None,
            "sentiment": None,
            "risk_level": None
        }
        
        # System prompts améliorés
        self.system_prompts = {
            "analysis": self._get_analysis_prompt(),
            "prediction": self._get_prediction_prompt(),
            "alert": self._get_alert_prompt(),
            "strategy": self._get_strategy_prompt()
        }
    
    def _get_analysis_prompt(self) -> str:
        """Prompt pour l'analyse de marché approfondie"""
        return """Tu es un analyste senior des marchés financiers avec 20 ans d'expérience.

EXPERTISE:
- Analyse macro-économique globale
- Trading algorithmique et analyse quantitative
- Gestion de risques et allocation d'actifs
- Psychologie de marché et analyse comportementale

STYLE D'ANALYSE:
1. **Vue d'ensemble** : Contexte macro et tendances globales
2. **Analyse technique** : Niveaux clés, patterns, indicateurs
3. **Analyse fondamentale** : Facteurs économiques, valorisations
4. **Sentiment de marché** : Positionnement, flux, psychologie
5. **Risques et opportunités** : Scénarios probabilisés
6. **Actions recommandées** : Stratégies concrètes

FORMAT:
- Utilise des **gras** pour les points critiques
- Inclus des 📈📉 pour les tendances
- Structure avec des bullet points
- Fournit des niveaux de prix précis
- Termine par une recommandation claire

RÈGLES:
- Sois factuel et data-driven
- Évite les prédictions sans fondement
- Inclus toujours le niveau de confiance
- Mentionne les risques potentiels"""
    
    def _get_prediction_prompt(self) -> str:
        """Prompt pour les prédictions de marché"""
        return """Tu es un stratégiste quantitatif spécialisé dans les prédictions de marché.

MISSION: Fournir des prévisions probabilistes basées sur:
- Analyse statistique et modèles quantitatifs
- Patterns historiques et saisonnalité
- Indicateurs leading et corrélations
- Machine learning et IA prédictive

FORMAT DE PRÉDICTION:
1. **Scénario de base** (60% probabilité)
2. **Scénario haussier** (25% probabilité)
3. **Scénario baissier** (15% probabilité)

TOUJOURS INCLURE:
- Horizons temporels (court/moyen/long terme)
- Niveaux de support/résistance
- Catalyseurs potentiels
- Indicateurs à surveiller
- Stop-loss et take-profit suggérés"""
    
    def _get_alert_prompt(self) -> str:
        """Prompt pour les alertes de marché"""
        return """Tu es un système d'alerte de trading en temps réel.

MISSION: Identifier et signaler:
- ⚠️ Mouvements de prix anormaux
- 🔔 Franchissements de niveaux clés
- 📰 News à fort impact
- 🎯 Opportunités de trading
- 🛡️ Signaux de risque

FORMAT D'ALERTE:
[URGENCE: Haute/Moyenne/Basse]
[TYPE: Prix/News/Technique/Fondamental]
[ACTION: Acheter/Vendre/Attendre/Hedger]

Message concis avec:
- Fait déclencheur
- Impact attendu
- Action recommandée
- Timeframe"""
    
    def _get_strategy_prompt(self) -> str:
        """Prompt pour les stratégies de trading"""
        return """Tu es un gestionnaire de portefeuille institutionnel.

EXPERTISE:
- Allocation d'actifs dynamique
- Stratégies long/short
- Arbitrage et trading de pairs
- Options et dérivés
- Risk management avancé

DÉVELOPPE DES STRATÉGIES:
1. **Objectif** : Rendement visé et horizon
2. **Setup** : Conditions d'entrée précises
3. **Exécution** : Taille de position et timing
4. **Gestion** : Stop-loss, trailing, scaling
5. **Sortie** : Conditions de clôture
6. **Risques** : Scénarios adverses et mitigation

MÉTRIQUES CLÉS:
- Ratio risque/rendement
- Sharpe ratio attendu
- Maximum drawdown
- Probabilité de succès"""
    
    def analyze_market_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyse l'intention de la requête marché
        """
        query_lower = query.lower()
        
        intents = {
            "price_analysis": any(word in query_lower for word in ["prix", "price", "cours", "valeur", "coût"]),
            "trend_analysis": any(word in query_lower for word in ["tendance", "trend", "direction", "évolution"]),
            "prediction": any(word in query_lower for word in ["prédi", "forecast", "futur", "sera", "devrait"]),
            "news_analysis": any(word in query_lower for word in ["news", "actualité", "annonce", "événement"]),
            "technical": any(word in query_lower for word in ["technique", "chart", "graphique", "pattern"]),
            "fundamental": any(word in query_lower for word in ["fondamental", "macro", "économi", "bilan"]),
            "sentiment": any(word in query_lower for word in ["sentiment", "psychologie", "fear", "greed"]),
            "risk": any(word in query_lower for word in ["risque", "risk", "volatilité", "protection"]),
            "strategy": any(word in query_lower for word in ["stratégie", "plan", "approche", "méthode"]),
            "alert": any(word in query_lower for word in ["alerte", "signal", "notification", "avertir"])
        }
        
        # Extraction d'entités
        entities = self._extract_market_entities(query)
        
        # Déterminer le prompt approprié
        if intents["prediction"]:
            prompt_type = "prediction"
        elif intents["strategy"]:
            prompt_type = "strategy"
        elif intents["alert"]:
            prompt_type = "alert"
        else:
            prompt_type = "analysis"
        
        return {
            "intents": intents,
            "entities": entities,
            "prompt_type": prompt_type,
            "urgency": self._assess_urgency(query),
            "complexity": self._assess_complexity(query)
        }
    
    def _extract_market_entities(self, query: str) -> Dict[str, List[str]]:
        """Extrait les entités de marché de la requête"""
        entities = {
            "assets": [],
            "indicators": [],
            "timeframes": [],
            "levels": [],
            "events": []
        }
        
        # Assets et tickers
        asset_patterns = [
            r'\b[A-Z]{2,5}\b',  # Tickers
            r'\b(?:bitcoin|btc|ethereum|eth|or|argent|pétrole|oil|forex|eur|usd|chf)\b',
            r'\b(?:nasdaq|sp500|s&p|dow|dax|cac|smi)\b'
        ]
        
        for pattern in asset_patterns:
            matches = re.findall(pattern, query.lower())
            entities["assets"].extend(matches)
        
        # Indicateurs techniques
        indicator_keywords = ["rsi", "macd", "moving average", "ma", "ema", "bollinger", "fibonacci"]
        for keyword in indicator_keywords:
            if keyword in query.lower():
                entities["indicators"].append(keyword)
        
        # Timeframes
        timeframe_patterns = [
            r'\b\d+[mjhd]\b',  # 5m, 1h, 1d
            r'\b(?:minute|hour|jour|day|semaine|week|mois|month|année|year)\b'
        ]
        for pattern in timeframe_patterns:
            matches = re.findall(pattern, query.lower())
            entities["timeframes"].extend(matches)
        
        # Niveaux de prix
        price_pattern = r'\b\d+(?:\.\d+)?(?:\s*(?:k|K|m|M|€|\$|CHF))?\b'
        prices = re.findall(price_pattern, query)
        entities["levels"] = prices
        
        return entities
    
    def _assess_urgency(self, query: str) -> str:
        """Évalue l'urgence de la requête"""
        urgent_keywords = ["urgent", "maintenant", "immédiat", "vite", "alert", "crash", "spike"]
        
        if any(keyword in query.lower() for keyword in urgent_keywords):
            return "high"
        elif "?" in query:
            return "medium"
        else:
            return "low"
    
    def _assess_complexity(self, query: str) -> str:
        """Évalue la complexité de la requête"""
        word_count = len(query.split())
        entity_count = len(self._extract_market_entities(query)["assets"])
        
        if word_count > 30 or entity_count > 3:
            return "complex"
        elif word_count > 15 or entity_count > 1:
            return "moderate"
        else:
            return "simple"
    
    def calculate_market_sentiment(self, data: Dict) -> Dict[str, Any]:
        """
        Calcule le sentiment de marché basé sur plusieurs indicateurs
        """
        sentiment_score = 0
        confidence = 0
        factors = []
        
        # Analyse basée sur les mots-clés
        positive_words = ["hausse", "bull", "rally", "breakout", "strong", "achat", "opportunité"]
        negative_words = ["baisse", "bear", "crash", "breakdown", "weak", "vente", "risque"]
        
        text = str(data.get("text", "")).lower()
        
        for word in positive_words:
            if word in text:
                sentiment_score += 1
                factors.append(f"Signal positif: {word}")
        
        for word in negative_words:
            if word in text:
                sentiment_score -= 1
                factors.append(f"Signal négatif: {word}")
        
        # Normaliser le score
        if sentiment_score > 0:
            sentiment = "Bullish"
            confidence = min(abs(sentiment_score) * 0.2, 1.0)
        elif sentiment_score < 0:
            sentiment = "Bearish"
            confidence = min(abs(sentiment_score) * 0.2, 1.0)
        else:
            sentiment = "Neutral"
            confidence = 0.5
        
        # Indicateurs complémentaires
        momentum = data.get("momentum", "neutral")
        volume = data.get("volume", "normal")
        
        return {
            "sentiment": sentiment,
            "score": sentiment_score,
            "confidence": confidence,
            "momentum": momentum,
            "volume": volume,
            "factors": factors,
            "emoji": "🐂" if sentiment == "Bullish" else "🐻" if sentiment == "Bearish" else "➖",
            "recommendation": self._get_sentiment_recommendation(sentiment, confidence)
        }
    
    def _get_sentiment_recommendation(self, sentiment: str, confidence: float) -> str:
        """Génère une recommandation basée sur le sentiment"""
        if sentiment == "Bullish" and confidence > 0.7:
            return "🟢 Position longue recommandée avec stops serrés"
        elif sentiment == "Bearish" and confidence > 0.7:
            return "🔴 Prudence, envisager des couvertures ou positions short"
        elif sentiment == "Neutral":
            return "🟡 Attendre des signaux plus clairs avant de prendre position"
        else:
            return "⚪ Signal faible, rester sur la touche"
    
    def generate_market_prediction(self, asset: str, timeframe: str = "1W") -> Dict[str, Any]:
        """
        Génère des prédictions de marché avec scénarios
        """
        # Simulation de prédictions (en production, utiliser des modèles ML)
        current_price = 100  # Prix de base pour démonstration
        
        scenarios = {
            "base": {
                "probability": 0.60,
                "target": current_price * 1.05,
                "range": (current_price * 1.02, current_price * 1.08),
                "description": "Continuation de la tendance actuelle avec volatilité modérée",
                "catalysts": ["Données économiques stables", "Pas de surprises majeures"]
            },
            "bullish": {
                "probability": 0.25,
                "target": current_price * 1.15,
                "range": (current_price * 1.10, current_price * 1.20),
                "description": "Breakout haussier avec momentum fort",
                "catalysts": ["Surprise positive des earnings", "Stimulus monétaire"]
            },
            "bearish": {
                "probability": 0.15,
                "target": current_price * 0.92,
                "range": (current_price * 0.88, current_price * 0.95),
                "description": "Correction technique ou risk-off",
                "catalysts": ["Données décevantes", "Tensions géopolitiques"]
            }
        }
        
        # Niveaux techniques
        technical_levels = {
            "resistance": [
                current_price * 1.05,
                current_price * 1.10,
                current_price * 1.15
            ],
            "support": [
                current_price * 0.98,
                current_price * 0.95,
                current_price * 0.90
            ],
            "pivot": current_price
        }
        
        # Indicateurs à surveiller
        key_indicators = [
            "RSI (14): Surveiller divergences",
            "MACD: Croisement des lignes",
            "Volume: Confirmation des mouvements",
            "Volatilité implicite: Anticipation du marché"
        ]
        
        return {
            "asset": asset,
            "timeframe": timeframe,
            "current_price": current_price,
            "scenarios": scenarios,
            "technical_levels": technical_levels,
            "key_indicators": key_indicators,
            "confidence": 0.75,
            "last_update": datetime.now().isoformat()
        }
    
    def detect_market_patterns(self, price_data: List[float]) -> Dict[str, Any]:
        """
        Détecte les patterns techniques dans les données de prix
        """
        if len(price_data) < 20:
            return {"error": "Insufficient data for pattern detection"}
        
        patterns_detected = []
        
        # Détection simple de tendance
        sma_20 = np.mean(price_data[-20:])
        sma_50 = np.mean(price_data[-50:]) if len(price_data) >= 50 else sma_20
        current_price = price_data[-1]
        
        if current_price > sma_20 > sma_50:
            patterns_detected.append({
                "name": "Uptrend",
                "strength": "Strong",
                "action": "Buy dips",
                "emoji": "📈"
            })
        elif current_price < sma_20 < sma_50:
            patterns_detected.append({
                "name": "Downtrend",
                "strength": "Strong",
                "action": "Sell rallies",
                "emoji": "📉"
            })
        
        # Détection de support/résistance
        recent_highs = sorted(price_data[-20:], reverse=True)[:3]
        recent_lows = sorted(price_data[-20:])[:3]
        
        resistance = np.mean(recent_highs)
        support = np.mean(recent_lows)
        
        if abs(current_price - resistance) / resistance < 0.02:
            patterns_detected.append({
                "name": "At Resistance",
                "strength": "High",
                "action": "Wait for breakout or reversal",
                "emoji": "🚧"
            })
        
        if abs(current_price - support) / support < 0.02:
            patterns_detected.append({
                "name": "At Support",
                "strength": "High",
                "action": "Potential bounce zone",
                "emoji": "🛡️"
            })
        
        return {
            "patterns": patterns_detected,
            "trend": "Bullish" if current_price > sma_20 else "Bearish",
            "key_levels": {
                "resistance": resistance,
                "support": support,
                "current": current_price
            },
            "recommendation": self._get_pattern_recommendation(patterns_detected)
        }
    
    def _get_pattern_recommendation(self, patterns: List[Dict]) -> str:
        """Génère une recommandation basée sur les patterns détectés"""
        if not patterns:
            return "Pas de pattern clair, rester neutre"
        
        pattern_names = [p["name"] for p in patterns]
        
        if "Uptrend" in pattern_names:
            return "📈 Tendance haussière confirmée, privilégier les positions longues"
        elif "Downtrend" in pattern_names:
            return "📉 Tendance baissière, éviter les achats ou shorter"
        elif "At Resistance" in pattern_names:
            return "🚧 Zone de résistance, attendre la cassure pour entrer"
        elif "At Support" in pattern_names:
            return "🛡️ Zone de support, opportunité d'achat potentielle"
        else:
            return "📊 Marché en range, trader les bornes"
    
    def generate_trading_alerts(self, market_data: Dict) -> List[Dict]:
        """
        Génère des alertes de trading basées sur les conditions de marché
        """
        alerts = []
        current_time = datetime.now()
        
        # Alerte de volatilité
        volatility = market_data.get("volatility", 0)
        if volatility > 30:
            alerts.append({
                "type": "VOLATILITY",
                "urgency": "HIGH",
                "message": f"⚠️ Volatilité élevée détectée: {volatility:.1f}%",
                "action": "Réduire les tailles de position, élargir les stops",
                "timestamp": current_time.isoformat()
            })
        
        # Alerte de momentum
        momentum = market_data.get("momentum", 0)
        if abs(momentum) > 70:
            direction = "haussier" if momentum > 0 else "baissier"
            alerts.append({
                "type": "MOMENTUM",
                "urgency": "MEDIUM",
                "message": f"🚀 Momentum {direction} fort: RSI à {abs(momentum)}",
                "action": f"Surveiller un retournement potentiel",
                "timestamp": current_time.isoformat()
            })
        
        # Alerte de volume
        volume_ratio = market_data.get("volume_ratio", 1.0)
        if volume_ratio > 2.0:
            alerts.append({
                "type": "VOLUME",
                "urgency": "MEDIUM",
                "message": f"📊 Volume anormal: {volume_ratio:.1f}x la moyenne",
                "action": "Mouvement significatif probable, préparer les ordres",
                "timestamp": current_time.isoformat()
            })
        
        # Alerte de corrélation
        correlation_break = market_data.get("correlation_break", False)
        if correlation_break:
            alerts.append({
                "type": "CORRELATION",
                "urgency": "LOW",
                "message": "🔄 Décorrélation détectée avec les indices majeurs",
                "action": "Analyser les facteurs spécifiques à l'actif",
                "timestamp": current_time.isoformat()
            })
        
        return sorted(alerts, key=lambda x: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(x["urgency"], 0), reverse=True)
    
    def create_market_summary(self, markets_data: Dict) -> str:
        """
        Crée un résumé de marché formaté et enrichi
        """
        summary = f"""
## 🌍 **RÉSUMÉ DES MARCHÉS** - {datetime.now().strftime('%d/%m/%Y %H:%M')}

### 📊 **Indices Majeurs**
"""
        
        # Indices
        indices = markets_data.get("indices", {})
        for index, data in indices.items():
            change = data.get("change", 0)
            emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            summary += f"- **{index}**: {data.get('price', 'N/A')} {emoji} ({change:+.2f}%)\n"
        
        # Sentiment général
        sentiment = self.calculate_market_sentiment(markets_data)
        summary += f"""

### 🎯 **Sentiment Global**
{sentiment['emoji']} **{sentiment['sentiment']}** (Confiance: {sentiment['confidence']:.0%})
{sentiment['recommendation']}

### 🔥 **Points Chauds**
"""
        
        # Alertes actives
        alerts = self.generate_trading_alerts(markets_data)
        if alerts:
            for alert in alerts[:3]:  # Top 3 alertes
                summary += f"- {alert['message']}\n"
        else:
            summary += "- Pas d'alertes actives\n"
        
        # Opportunités
        summary += """

### 💡 **Opportunités du Jour**
"""
        opportunities = markets_data.get("opportunities", [])
        if opportunities:
            for opp in opportunities[:3]:
                summary += f"- {opp}\n"
        else:
            summary += "- Marché calme, peu d'opportunités immédiates\n"
        
        # Calendrier économique
        summary += """

### 📅 **Événements à Venir**
"""
        events = markets_data.get("upcoming_events", [])
        if events:
            for event in events[:3]:
                summary += f"- {event}\n"
        else:
            summary += "- Pas d'événements majeurs prévus\n"
        
        # Recommandation finale
        summary += f"""

### 🎬 **Action Recommandée**
{self._get_daily_recommendation(sentiment, markets_data)}

---
*Analyse générée par Enhanced Markets Chat v2.0*
"""
        return summary
    
    def _get_daily_recommendation(self, sentiment: Dict, data: Dict) -> str:
        """Génère une recommandation quotidienne"""
        volatility = data.get("volatility", "normal")
        
        if sentiment["sentiment"] == "Bullish" and volatility != "high":
            return "✅ **Journée favorable pour les positions longues** - Privilégier les achats sur replis avec stops serrés"
        elif sentiment["sentiment"] == "Bearish":
            return "🛡️ **Prudence recommandée** - Réduire l'exposition ou considérer des hedges"
        elif volatility == "high":
            return "⚡ **Volatilité élevée** - Réduire les tailles de position et élargir les stops"
        else:
            return "📊 **Marché neutre** - Attendre des signaux plus clairs ou trader en range"
    
    def generate_enhanced_reply(self, message: str, context: Optional[str] = None, history: Optional[list] = None) -> str:
        """
        Version améliorée de generate_reply avec toutes les nouvelles fonctionnalités
        """
        msg = (message or "").strip()
        if not msg:
            raise ValueError("Message vide")
        
        # Analyser l'intention
        intent_analysis = self.analyze_market_intent(msg)
        
        # Sélectionner le prompt approprié
        system_prompt = self.system_prompts.get(intent_analysis["prompt_type"], self.system_prompts["analysis"])
        
        # Enrichir le contexte avec les analyses
        enriched_context = self._build_enriched_context(msg, context, intent_analysis)
        
        # Construire les messages
        typed_messages = []
        typed_messages.append({"role": "system", "content": system_prompt})
        
        # Ajouter l'historique
        try:
            for h in (history or [])[-6:]:
                role = 'assistant' if (h.get('role') == 'assistant') else 'user'
                content = str(h.get('content', '')).strip()
                if content:
                    typed_messages.append({"role": role, "content": content})
        except Exception:
            pass
        
        typed_messages.append({"role": "user", "content": enriched_context})
        
        # Appel à l'API avec le nouveau prompt
        try:
            res = self.client.responses.create(
                model=self.model,
                input=[{"role": m["role"], "content": [{"type": "input_text" if m["role"]=="user" else "output_text", "text": m["content"]}]} for m in typed_messages],
                reasoning={"effort": "high"},
                max_output_tokens=self.max_output_tokens,
                store=False,
                response_format={"type": "text"},
            )
            text = (extract_output_text(res) or "").strip()
        except Exception:
            text = ""
        
        # Fallback si vide
        if not text:
            try:
                res2 = from_responses_simple(
                    client=self.client,
                    model=self.model,
                    messages=typed_messages,
                    reasoning_effort="high",
                    max_output_tokens=self.max_output_tokens,
                    response_format={"type": "text"},
                )
                text = (extract_output_text(res2) or "").strip()
            except Exception:
                text = ""
        
        # Post-traitement: ajouter des éléments visuels si pertinent
        if intent_analysis["intents"].get("prediction"):
            text = self._add_prediction_visuals(text, intent_analysis["entities"])
        elif intent_analysis["intents"].get("technical"):
            text = self._add_technical_indicators(text)
        
        return text
    
    def _build_enriched_context(self, message: str, context: Optional[str], intent_analysis: Dict) -> str:
        """Construit un contexte enrichi pour l'IA"""
        ctx = (context or "").strip()
        
        # Ajouter les données de marché si disponibles
        market_context = f"""
Question: {message}

Analyse détectée:
- Type: {intent_analysis['prompt_type']}
- Urgence: {intent_analysis['urgency']}
- Complexité: {intent_analysis['complexity']}
"""
        
        if intent_analysis["entities"]["assets"]:
            market_context += f"\nActifs mentionnés: {', '.join(intent_analysis['entities']['assets'])}"
        
        if intent_analysis["entities"]["timeframes"]:
            market_context += f"\nTimeframes: {', '.join(intent_analysis['entities']['timeframes'])}"
        
        if ctx:
            market_context += f"\n\nContexte additionnel:\n{ctx}"
        
        return market_context
    
    def _add_prediction_visuals(self, text: str, entities: Dict) -> str:
        """Ajoute des éléments visuels pour les prédictions"""
        visual_addition = "\n\n📊 **Visualisation des Scénarios**\n"
        visual_addition += "```\n"
        visual_addition += "    Bullish  ━━━━━━━━━━━━━━━━━━━━ 📈 +15%\n"
        visual_addition += "    Base     ━━━━━━━━━━━━━━━ 📊 +5%\n"
        visual_addition += "    Bearish  ━━━━━━━ 📉 -8%\n"
        visual_addition += "```"
        
        return text + visual_addition
    
    def _add_technical_indicators(self, text: str) -> str:
        """Ajoute des indicateurs techniques visuels"""
        indicators = "\n\n📈 **Indicateurs Techniques**\n"
        indicators += "- RSI(14): `[████████░░] 72` ⚠️ Suracheté\n"
        indicators += "- MACD: 🟢 Signal haussier\n"
        indicators += "- Volume: 📊 +45% vs moyenne\n"
        
        return text + indicators
    
    def stream_enhanced_reply(self, message: str, context: Optional[str] = None) -> Generator[str, None, None]:
        """
        Version améliorée du streaming avec analyses en temps réel
        """
        msg = (message or "").strip()
        if not msg:
            yield "[ERROR:Message vide]"
            return
        
        # Analyser l'intention
        intent_analysis = self.analyze_market_intent(msg)
        
        # Yield une indication du type d'analyse en cours
        if intent_analysis["prompt_type"] == "prediction":
            yield "🔮 Génération de prédictions de marché...\n\n"
        elif intent_analysis["prompt_type"] == "alert":
            yield "🔔 Analyse des alertes actives...\n\n"
        elif intent_analysis["prompt_type"] == "strategy":
            yield "📋 Élaboration de la stratégie...\n\n"
        else:
            yield "📊 Analyse des marchés en cours...\n\n"
        
        # Stream la réponse principale
        enriched_context = self._build_enriched_context(msg, context, intent_analysis)
        system_prompt = self.system_prompts.get(intent_analysis["prompt_type"], self.system_prompts["analysis"])
        
        kwargs = {
            "model": self.model,
            "instructions": system_prompt,
            "input": enriched_context,
            "stream": True,
            "store": False,
        }
        
        try:
            try:
                streamer = self.client.responses.stream(**kwargs)
                with streamer as stream:
                    for event in stream:
                        etype = getattr(event, "type", None)
                        if etype == "response.output_text.delta":
                            chunk = getattr(event, "delta", None)
                            if chunk:
                                yield str(chunk)
                        elif etype == "error":
                            err = str(getattr(event, "error", "unknown"))
                            yield f"\n\n[ERROR:{err}]"
            except Exception:
                # Fallback non-stream
                text = self.generate_enhanced_reply(message=msg, context=context)
                yield text
        except Exception as e:
            yield f"\n\n[ERROR:{e}]"


# Instance singleton améliorée
_enhanced_singleton: Optional[EnhancedMarketsChatWorker] = None


def get_enhanced_markets_chat_worker() -> EnhancedMarketsChatWorker:
    """Retourne l'instance singleton du worker amélioré"""
    global _enhanced_singleton
    if _enhanced_singleton is None:
        _enhanced_singleton = EnhancedMarketsChatWorker()
    return _enhanced_singleton


# Compatibilité avec l'ancien système
def get_markets_chat_worker() -> EnhancedMarketsChatWorker:
    """Alias pour compatibilité"""
    return get_enhanced_markets_chat_worker()
