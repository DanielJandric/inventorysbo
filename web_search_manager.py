#!/usr/bin/env python3
"""
Module de gestion de la recherche web OpenAI pour les informations financières
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSearchType(Enum):
    """Types de recherche web disponibles"""
    MARKET_DATA = "market_data"
    FINANCIAL_NEWS = "financial_news"
    STOCK_ANALYSIS = "stock_analysis"
    ECONOMIC_INDICATORS = "economic_indicators"
    CRYPTO_MARKET = "crypto_market"
    FOREX_MARKET = "forex_market"
    COMMODITIES = "commodities"
    CENTRAL_BANKS = "central_banks"
    GEOPOLITICAL = "geopolitical"

@dataclass
class WebSearchResult:
    """Résultat d'une recherche web"""
    query: str
    content: str
    citations: List[Dict[str, Any]]
    search_call_id: str
    timestamp: str
    search_type: WebSearchType
    domains_searched: Optional[List[str]] = None
    user_location: Optional[Dict[str, str]] = None

@dataclass
class FinancialMarketData:
    """Données de marché financier structurées"""
    indices: Dict[str, Dict[str, Any]]
    bonds: Dict[str, Dict[str, Any]]
    crypto: Dict[str, Dict[str, Any]]
    forex: Dict[str, Dict[str, Any]]
    commodities: Dict[str, Dict[str, Any]]
    news: List[Dict[str, Any]]
    timestamp: str
    source: str

class OpenAIWebSearchManager:
    """Gestionnaire de recherche web OpenAI pour les informations financières"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
        
    def search_financial_markets(self, 
                                search_type: WebSearchType = WebSearchType.MARKET_DATA,
                                user_location: Optional[Dict[str, str]] = None,
                                search_context_size: str = "medium") -> Optional[WebSearchResult]:
        """
        Effectue une recherche web pour les informations financières
        
        Args:
            search_type: Type de recherche à effectuer
            user_location: Localisation de l'utilisateur pour affiner les résultats
            search_context_size: Taille du contexte de recherche (low/medium/high)
            
        Returns:
            WebSearchResult ou None en cas d'erreur
        """
        try:
            # Construire la requête selon le type de recherche
            query = self._build_search_query(search_type)
            
            tool_candidates = [{"type": "web_search"}, {"type": "web_search_preview"}]
            response = None
            last_err = None
            for t in tool_candidates:
                try:
                    if user_location:
                        t = {**t, "user_location": {"type": "approximate", **user_location}}
                    response = self.openai_client.responses.create(
                        model=os.getenv("AI_MODEL", "gpt-5"),
                        tools=[t],
                        input=[{"role":"user","content":[{"type":"input_text","text": query}]}],
                        reasoning={"effort": "high"}
                    )
                    break
                except Exception as e:
                    last_err = e
                    continue
            if response is None:
                raise last_err or RuntimeError("web_search tool unavailable")
            
            # Traiter la réponse
            return self._process_web_search_response(response, search_type, query)
            
        except Exception as e:
            logger.error(f"Erreur recherche web financière: {e}")
            return None
    
    def _build_search_query(self, search_type: WebSearchType) -> str:
        """Construit la requête de recherche selon le type"""
        
        current_date = datetime.now().strftime('%d/%m/%Y')
        
        queries = {
            WebSearchType.MARKET_DATA: f"""Recherche les données de marché actuelles pour {current_date}:
- Indices boursiers (S&P 500, NASDAQ, Dow Jones, Euro Stoxx 50, DAX, CAC 40, Swiss Market Index)
- Rendements obligataires (US 10Y, Bund 10Y, OAT 10Y, BTP 10Y)
- Cryptoactifs (Bitcoin, Ethereum, capitalisation globale)
- Devises (EUR/USD, USD/CHF, GBP/USD)
- Commodities (Or, Pétrole)
Fournis les données avec les variations et tendances actuelles.""",
            
            WebSearchType.FINANCIAL_NEWS: f"""Recherche les actualités financières importantes du {current_date}:
- Actualités macroéconomiques
- Décisions de banques centrales
- Rapports de résultats d'entreprises
- Événements géopolitiques impactant les marchés
- Tendances sectorielles""",
            
            WebSearchType.STOCK_ANALYSIS: f"""Recherche les analyses boursières actuelles pour {current_date}:
- Recommandations d'analystes
- Revisions de prix cibles
- Changements de notation
- Tendances sectorielles
- Opportunités d'investissement""",
            
            WebSearchType.ECONOMIC_INDICATORS: f"""Recherche les indicateurs économiques récents:
- PIB, inflation, chômage
- Indices de confiance
- Données de consommation
- Indicateurs de production
- Tendances économiques globales""",
            
            WebSearchType.CRYPTO_MARKET: f"""Recherche les données du marché crypto pour {current_date}:
- Prix Bitcoin, Ethereum et autres cryptos majeures
- Capitalisation globale
- Volumes d'échange
- Actualités réglementaires
- Tendances DeFi et NFT""",
            
            WebSearchType.FOREX_MARKET: f"""Recherche les données du marché des changes pour {current_date}:
- Paires de devises majeures
- Corrélations avec les marchés actions
- Interventions de banques centrales
- Tendances de carry trade
- Volatilité des devises""",
            
            WebSearchType.COMMODITIES: f"""Recherche les données des matières premières pour {current_date}:
- Prix du pétrole (Brent, WTI)
- Métaux précieux (Or, Argent, Platine)
- Métaux industriels (Cuivre, Aluminium)
- Produits agricoles
- Tendances de l'énergie""",
            
            WebSearchType.CENTRAL_BANKS: f"""Recherche les actualités des banques centrales:
- Décisions de politique monétaire
- Communications des gouverneurs
- Perspectives d'inflation
- Évolutions des taux directeurs
- Impact sur les marchés""",
            
            WebSearchType.GEOPOLITICAL: f"""Recherche les événements géopolitiques impactant les marchés:
- Tensions internationales
- Accords commerciaux
- Élections importantes
- Sanctions économiques
- Impact sur les marchés financiers"""
        }
        
        return queries.get(search_type, queries[WebSearchType.MARKET_DATA])
    
    def _process_web_search_response(self, response, search_type: WebSearchType, original_query: str) -> Optional[WebSearchResult]:
        """Traite la réponse de recherche web OpenAI"""
        try:
            # Extraire les informations de la réponse
            web_search_call = None
            message_content = None
            citations = []
            
            for output_item in response.output:
                if output_item.type == "web_search_call":
                    web_search_call = output_item
                elif output_item.type == "message":
                    message_content = output_item.content[0].text
                    # Extraire les citations
                    if hasattr(output_item.content[0], 'annotations'):
                        for annotation in output_item.content[0].annotations:
                            if annotation.type == "url_citation":
                                citations.append({
                                    "url": annotation.url,
                                    "title": annotation.title,
                                    "start_index": annotation.start_index,
                                    "end_index": annotation.end_index
                                })
            
            if not message_content:
                logger.error("Contenu de réponse vide")
                return None
            
            # Construire le résultat
            result = WebSearchResult(
                query=original_query,
                content=message_content,
                citations=citations,
                search_call_id=web_search_call.id if web_search_call else "",
                timestamp=datetime.now().isoformat(),
                search_type=search_type,
                domains_searched=web_search_call.domains if web_search_call else None
            )
            
            logger.info(f"✅ Recherche web réussie pour {search_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur traitement réponse web search: {e}")
            return None
    
    def get_comprehensive_market_briefing(self, user_location: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Génère un briefing de marché complet en utilisant la recherche web
        
        Args:
            user_location: Localisation de l'utilisateur
            
        Returns:
            Contenu du briefing ou None en cas d'erreur
        """
        try:
            current_date = datetime.now().strftime('%d/%m/%Y')
            
            # PROMPT optimisé (analyste senior) – focus sur la séance du jour
            prompt = f"""# PROMPT OPTIMISÉ : ANALYSTE SENIOR MARCHÉS FINANCIERS (Date: {current_date})

## 🎯 IDENTITÉ ET MISSION

Tu es un **Directeur de Recherche Senior** combinant expertise en:
- **Finance quantitative** (20+ ans d'expérience sell-side)
- **Géopolitique appliquée** (focus sur impacts marchés)
- **Intelligence artificielle** (analyse prédictive et pattern recognition)

**Audience cible**: C-Suite, gestionnaires de fonds institutionnels, traders professionnels
**Objectif**: Produire une analyse **actionnable** avec signaux de trading clairs

## 🧠 CADRE ANALYTIQUE MULTI-DIMENSIONNEL

### 1. HIÉRARCHIE COGNITIVE
Applique une analyse à 4 niveaux:
1. **Niveau Micro**: Prix, volumes, indicateurs techniques
2. **Niveau Méso**: Secteurs, corrélations inter-marchés, flux
3. **Niveau Macro**: Politique monétaire, données économiques
4. **Niveau Méta**: Géopolitique, changements structurels, régimes de marché

### 2. INTÉGRATION TEMPORELLE
Pour chaque insight, considère:
- **T-1**: Contexte historique et momentum
- **T0**: État actuel et déséquilibres
- **T+1**: Scénarios probabilistes (base/bull/bear)

### 3. ANALYSE CAUSALE
Pour chaque mouvement significatif (>0.5σ):
- Identifie la **cause primaire** (catalyst)
- Trace les **effets de second ordre**
- Anticipe les **réactions en chaîne**

## 🔍 STRATÉGIE DE RECHERCHE WEB INTELLIGENTE

Active le tool `web_search` si besoin (données manquantes critiques, anomalies >3σ, événements géopolitiques, validations critiques). Priorise sources Tier 1 (Bloomberg, Reuters, FT, WSJ). Limite à 5 requêtes.

Format de requête optimal: "[ACTIF/ÉVÉNEMENT] + [TIMEFRAME] + [IMPACT/ANALYSE]". Exemple: "NVDA earnings Q4 2024 market impact analysis".

## 📊 RÈGLES DE DONNÉES STRICTES

Hiérarchie: 1) `market_snapshot` prioritaire, 2) web_search pour contexte, 3) jamais inventer ("N/D" avec explication). Pour signaux: divergences prix/volume (>20% 20j), sectorielles (z>2), géographiques (>1σ).

## 🎨 FORMAT DE SORTIE

Renvoie un JSON complet selon ce schéma (extrait) avec sections: `meta_analysis`, `executive_dashboard` (dont `top_trades`, `snapshot_metrics`), `deep_analysis` (narrative 3000+ chars, rotation sectorielle, corrélations, focus IA, chess géopolitique), `quantitative_signals`, `risk_management`, `actionable_summary`, `metadata` (timestamps, qualité des données, prochaine mise à jour).

Inclure un marquage explicite des sources: `source_type` (market_data/web_search/hybrid), `search_confidence`, `search_queries_used`.

## 🎯 TÂCHE

Construit un briefing pour la séance du jour ({current_date}), en te basant sur des données RÉELLES:
- Indices boursiers (S&P 500, NASDAQ, Dow Jones, Euro Stoxx 50, DAX, CAC 40, Swiss Market Index)
- Rendements obligataires (US 2Y/10Y, Bund/OAT/BTP 10Y)
- Cryptoactifs (BTC, ETH, capitalisation globale)
- Devises (DXY, EUR/USD, USD/CHF, GBP/USD)
- Commodities (Brent/WTI, Or)
- Macro/banques centrales/géopolitique (stats, décisions, tensions)

Rappels de style: précision, ton trading floor, pas de blabla. Si une classe n'a pas bougé, dis-le clairement. Génère le JSON structuré (aucun texte hors-JSON).
"""

            # Effectuer la recherche via OpenAI avec fallback de tool
            tool_candidates = [{"type": "web_search"}, {"type": "web_search_preview"}]
            response = None
            last_err = None
            for t in tool_candidates:
                try:
                    if user_location:
                        t = {**t, "user_location": {"type": "approximate", **user_location}}
                    response = self.openai_client.responses.create(
                        model=os.getenv("AI_MODEL", "gpt-5"),
                        tools=[t],
                        input=[{"role":"user","content":[{"type":"input_text","text": prompt}]}],
                        reasoning={"effort": "high"}
                    )
                    break
                except Exception as e:
                    last_err = e
                    continue
            if response is None:
                raise last_err or RuntimeError("web_search tool unavailable")
            
            # Extraire le contenu
            for output_item in response.output:
                if output_item.type == "message":
                    return output_item.content[0].text
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur génération briefing complet: {e}")
            return None
    
    def search_specific_stock(self, symbol: str, user_location: Optional[Dict[str, str]] = None) -> Optional[WebSearchResult]:
        """
        Recherche des informations spécifiques sur une action
        
        Args:
            symbol: Symbole de l'action (ex: AAPL, TSLA)
            user_location: Localisation de l'utilisateur
            
        Returns:
            WebSearchResult ou None
        """
        try:
            query = f"""Recherche les informations actuelles sur l'action {symbol}:
- Prix actuel et variations
- Volume d'échange
- Ratios financiers (P/E, P/B, etc.)
- Actualités récentes
- Analyses d'analystes
- Perspectives et recommandations
Fournis les données les plus récentes disponibles."""
            
            return self.search_financial_markets(
                search_type=WebSearchType.STOCK_ANALYSIS,
                user_location=user_location
            )
            
        except Exception as e:
            logger.error(f"Erreur recherche action {symbol}: {e}")
            return None
    
    def get_market_alert(self, alert_type: str = "breaking_news") -> Optional[WebSearchResult]:
        """
        Recherche des alertes de marché en temps réel
        
        Args:
            alert_type: Type d'alerte (breaking_news, market_moves, etc.)
            
        Returns:
            WebSearchResult ou None
        """
        try:
            query = f"""Recherche les alertes de marché en temps réel:
- Actualités importantes qui viennent de sortir
- Mouvements de marché significatifs
- Annonces de banques centrales
- Événements géopolitiques impactant les marchés
- Ruptures de tendance
Fournis les informations les plus récentes et importantes."""
            
            return self.search_financial_markets(
                search_type=WebSearchType.FINANCIAL_NEWS
            )
            
        except Exception as e:
            logger.error(f"Erreur recherche alertes: {e}")
            return None

def create_web_search_manager(openai_client) -> OpenAIWebSearchManager:
    """Factory function pour créer un gestionnaire de recherche web"""
    return OpenAIWebSearchManager(openai_client) 