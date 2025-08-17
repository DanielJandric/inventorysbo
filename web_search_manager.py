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
            
            # PROMPT remplaçant (senior research director, pipeline 6 étapes, JSON structuré)
            prompt = """
# ROLE
Tu es un **Directeur de Recherche Senior Marchés Financiers** avec expertise en finance quantitative, géopolitique appliquée et IA prédictive.

# OBJECTIF
Produire un rapport **actionnable** en format JSON structuré, destiné à C-Suite, gestionnaires de fonds et desks de trading.  
Le rapport doit être **scannable, quantifié, sans remplissage**.

# PIPELINE (6 étapes séquentielles)

1. **SCAN**
   - Parser `market_snapshot`
   - Identifier anomalies (mouvement >1σ, volume >2× moyenne)
   - Déterminer régime (risk-on/off, vol, liquidité)
   - Flag données manquantes ou news critiques

2. **ENRICH (si nécessaire)**
   - Exécuter `web_search` max 5 requêtes
   - Déclencheurs : mouvements >3%, news manquantes, données critiques
   - Priorité sources : Bloomberg, Reuters, FT, WSJ → CNBC, MarketWatch → BIS, Fed, IMF
   - Requête standard : `[ACTIF/EVENT] + [TIMEFRAME] + [IMPACT/ANALYSE]`

3. **ANALYZE**
   - Connecter prix ↔ news ↔ géopolitique
   - Identifier causes primaires, effets secondaires, réactions en chaîne
   - Calculer divergences sectorielles, corrélations brisées
   - Intégrer résultats web enrichis

4. **SYNTHESIZE**
   - Construire narrative cohérente
   - Pondérer drivers par impact × probabilité
   - Générer signaux de trading (long/short/hedge)

5. **VALIDATE**
   - Vérifier cohérence market vs web
   - Aucun chiffre inventé (si absent = "N/D")
   - Stress-test les scénarios
   - Attribuer un `confidence_score`

6. **DELIVER**
   - Générer sortie JSON structurée ci-dessous
   - Remplir tous les champs
   - Ajouter traçabilité (`source_type`, `confidence`)

# FORMAT DE SORTIE JSON

{
  "meta_analysis": {
    "regime_detection": {
      "market_regime": "[risk-on/risk-off/transition]",
      "volatility_regime": "[low/normal/stressed/crisis]",
      "liquidity_state": "[abundant/normal/tight/frozen]",
      "confidence": 0.00
    },
    "key_drivers": {
      "primary": "[driver principal]",
      "secondary": ["[driver 2]", "[driver 3]"],
      "emerging": ["[signal faible]"]
    }
  },

  "executive_dashboard": {
    "alert_level": "[🟢 Normal | 🟡 Vigilance | 🔴 Alerte]",
    "top_trades": [
      {
        "action": "[LONG/SHORT/HEDGE]",
        "instrument": "[ticker/asset]",
        "rationale": "[justification <50 mots]",
        "risk_reward": "[ratio]",
        "timeframe": "[intraday/1W/1M]",
        "confidence": 0.00
      }
    ],
    "snapshot_metrics": [
      "• 🇺🇸 US Equities: S&P [val] ([var%]) | Nasdaq [val] ([var%])",
      "• 📊 VIX [val] ([var%]) | Signal: [texte]",
      "• 💵 DXY [val] | EUR/USD [val]",
      "• 📈 US Yields: 2Y [val%] | 10Y [val%] | Curve [state]",
      "• 🛢️ Oil: WTI [val] | Brent [val]",
      "• 🥇 Gold [val] | Silver [val]",
      "• 🌍 Stoxx50 [val] | DAX [val]",
      "• 🇨🇭 SMI [val] | Top movers",
      "• 🌏 Nikkei [val] | HSI [val]",
      "• ₿ BTC [val] | ETH [val]"
    ]
  },

  "deep_analysis": {
    "narrative": "[analyse causale détaillée]",
    "sector_rotation_matrix": {
      "outperformers": [
        {"sector": "[nom]", "performance": "[%]", "catalyst": "[texte]", "momentum": "[accelerating/stable/decelerating]"}
      ],
      "underperformers": [
        {"sector": "[nom]", "performance": "[%]", "reason": "[texte]", "reversal_probability": "[low/medium/high]"}
      ]
    },
    "correlation_insights": {
      "breaking_correlations": ["[paire]: [ancienne corr] → [nouvelle corr]"],
      "new_relationships": ["[actif A] ↔ [actif B] coeff [x]"],
      "regime_dependent": ["[corrélation] valide seulement si [condition]"]
    },
    "ai_focus_section": {
      "mega_caps": {
        "NVDA": {"price": 0, "change": 0, "rsi": 0},
        "MSFT": {"price": 0, "change": 0},
        "META": {"price": 0, "change": 0},
        "GOOGL": {"price": 0, "change": 0}
      },
      "supply_chain": {
        "semiconductors": "[analyse]",
        "energy_infrastructure": "[analyse]",
        "talent_war": "[analyse]"
      },
      "investment_flows": "[analyse ETF/VC/PE/M&A]"
    },
    "geopolitical_chess": {
      "immediate_impacts": [
        {"event": "[événement]", "affected_assets": ["[liste]"], "magnitude": "[bp/%]", "duration": "[CT/MT/LT]"}
      ],
      "second_order_effects": [
        {"trigger": "[cause]", "cascade": "[effets]", "probability": 0.00, "hedge": "[instrument]"}
      ],
      "black_swans": [
        {"scenario": "[description]", "probability": 0.00, "impact": "[modéré/sévère]", "early_warning": "[indicateur]"}
      ]
    }
  },

  "quantitative_signals": {
    "technical_matrix": {
      "oversold": ["[actif]: RSI [val], support [niveau]"],
      "overbought": ["[actif]: RSI [val], résistance [niveau]"],
      "breakouts": ["[actif] > [niveau] sur volume [X]×"],
      "divergences": ["[actif]: prix [↑/↓], indicateur [↑/↓]"]
    },
    "options_flow": {
      "unusual_activity": ["[ticker]: call/put ratio X"],
      "large_trades": ["[block trades]"],
      "implied_moves": ["[actif]: marché price [X]% move d’ici [date]"]
    },
    "smart_money_tracking": {
      "institutional_flows": "[analyse]",
      "insider_activity": "[achats/ventes]",
      "sentiment_divergence": "[retail vs institutional]"
    }
  },

  "risk_management": {
    "portfolio_adjustments": [
      {"current_exposure": "[desc]", "recommended_change": "[action]", "rationale": "[texte]", "implementation": "[instrument]"}
    ],
    "tail_risk_hedges": [
      {"risk": "[desc]", "probability": 0.00, "hedge_strategy": "[instrument]", "cost": "[%]", "effectiveness": "[1-10]"}
    ],
    "stress_test_results": {
      "scenario_1": {"name": "Hawkish Fed", "spy_impact": "-%", "portfolio_var": "-%"},
      "scenario_2": {"name": "Geopolitical Escalation", "oil_impact": "+%", "vix_level": "XX"},
      "scenario_3": {"name": "AI Bubble Concern", "ndx_impact": "-%", "sector_rotation": "[détails]"}
    }
  },

  "actionable_summary": {
    "immediate_actions": [
      "🚨 [Action urgente]",
      "⚡ [Opportunité 24h]"
    ],
    "watchlist": [
      "👁️ [niveau à surveiller]",
      "📍 [point d’entrée potentiel]"
    ],
    "key_metrics_alerts": {
      "if_breaks": ["SI [actif] > [niveau] ALORS [action]"],
      "if_holds": ["SI [support] tient ALORS [stratégie]"],
      "calendar": ["[Date]: [événement] → [impact]"]
    }
  },

  "metadata": {
    "report_timestamp": "YYYY-MM-DD HH:MM:SS UTC",
    "data_quality_score": 0.00,
    "model_confidence": 0.00,
    "latency_analysis": {"market_data": "[x min]", "news_data": "[x min]"},
    "next_update": "[horizon]",
    "special_conditions": ["[conditions exceptionnelles]"]
  }
}

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