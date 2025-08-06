"""
Google Search API Manager for Financial Market Reports and Daily News
Provides integration with Google Custom Search API for real-time financial information
"""

import os
import requests
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum

# Configuration du logging
logger = logging.getLogger(__name__)

class GoogleSearchType(Enum):
    """Types de recherche Google disponibles"""
    MARKET_NEWS = "market_news"
    FINANCIAL_REPORTS = "financial_reports"
    STOCK_ANALYSIS = "stock_analysis"
    ECONOMIC_INDICATORS = "economic_indicators"
    CRYPTO_NEWS = "crypto_news"
    FOREX_NEWS = "forex_news"
    COMMODITIES_NEWS = "commodities_news"

@dataclass
class GoogleSearchResult:
    """Résultat d'une recherche Google"""
    title: str
    link: str
    snippet: str
    source: str
    published_date: Optional[str] = None
    relevance_score: float = 0.0

@dataclass
class MarketReport:
    """Rapport de marché structuré"""
    title: str
    summary: str
    key_points: List[str]
    market_sentiment: str
    sources: List[str]
    timestamp: str
    market_impact: str

@dataclass
class DailyNewsItem:
    """Élément de nouvelle quotidienne"""
    headline: str
    summary: str
    category: str
    source: str
    url: str
    published_date: str
    importance_level: str

class GoogleSearchManager:
    """Gestionnaire pour l'API de recherche Google"""
    
    def __init__(self, api_key: str, search_engine_id: str):
        """
        Initialise le gestionnaire de recherche Google
        
        Args:
            api_key: Clé API Google Custom Search
            search_engine_id: ID du moteur de recherche personnalisé
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # Configuration des sources financières fiables
        self.financial_sources = [
            "reuters.com",
            "bloomberg.com", 
            "cnbc.com",
            "marketwatch.com",
            "yahoo.com/finance",
            "investing.com",
            "seekingalpha.com",
            "financialtimes.com",
            "wsj.com",
            "ft.com"
        ]
        
        logger.info("✅ Google Search Manager initialisé")
    
    def search_financial_markets(self, 
                                query: str, 
                                search_type: GoogleSearchType = GoogleSearchType.MARKET_NEWS,
                                max_results: int = 10,
                                date_restrict: str = "d1") -> List[GoogleSearchResult]:
        """
        Effectue une recherche sur les marchés financiers
        
        Args:
            query: Requête de recherche
            search_type: Type de recherche
            max_results: Nombre maximum de résultats
            date_restrict: Restriction de date (d1=jour, w1=semaine, m1=mois)
            
        Returns:
            Liste des résultats de recherche
        """
        try:
            # Construction de la requête selon le type
            enhanced_query = self._build_enhanced_query(query, search_type)
            
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': enhanced_query,
                'num': min(max_results, 10),  # Google limite à 10 par requête
                'dateRestrict': date_restrict,
                'sort': 'date:r:20240101:20991231',  # Tri par date récente
                'fields': 'items(title,link,snippet,pagemap/metatags,pagemap/newsarticle)'
            }
            
            logger.info(f"🔍 Recherche Google: {enhanced_query}")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = self._process_google_response(data, search_type)
            
            logger.info(f"✅ {len(results)} résultats trouvés")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur requête Google Search: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur recherche Google: {e}")
            return []
    
    def _build_enhanced_query(self, base_query: str, search_type: GoogleSearchType) -> str:
        """Construit une requête enrichie selon le type de recherche"""
        
        # Mots-clés spécifiques par type
        type_keywords = {
            GoogleSearchType.MARKET_NEWS: "financial markets news today",
            GoogleSearchType.FINANCIAL_REPORTS: "financial reports earnings quarterly",
            GoogleSearchType.STOCK_ANALYSIS: "stock analysis price target",
            GoogleSearchType.ECONOMIC_INDICATORS: "economic indicators GDP inflation",
            GoogleSearchType.CRYPTO_NEWS: "cryptocurrency bitcoin ethereum news",
            GoogleSearchType.FOREX_NEWS: "forex currency exchange rates",
            GoogleSearchType.COMMODITIES_NEWS: "commodities oil gold silver"
        }
        
        # Sources fiables
        sources_query = " OR ".join([f"site:{source}" for source in self.financial_sources])
        
        # Construction de la requête finale
        enhanced_query = f'"{base_query}" {type_keywords.get(search_type, "")} ({sources_query})'
        
        return enhanced_query
    
    def _process_google_response(self, data: Dict, search_type: GoogleSearchType) -> List[GoogleSearchResult]:
        """Traite la réponse de l'API Google"""
        results = []
        
        if 'items' not in data:
            return results
        
        for item in data['items']:
            try:
                # Extraction des métadonnées
                title = item.get('title', '')
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                
                # Extraction de la source
                source = self._extract_source(link)
                
                # Extraction de la date de publication
                published_date = self._extract_published_date(item)
                
                # Calcul du score de pertinence
                relevance_score = self._calculate_relevance_score(item, search_type)
                
                result = GoogleSearchResult(
                    title=title,
                    link=link,
                    snippet=snippet,
                    source=source,
                    published_date=published_date,
                    relevance_score=relevance_score
                )
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur traitement résultat: {e}")
                continue
        
        # Tri par score de pertinence
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results
    
    def _extract_source(self, url: str) -> str:
        """Extrait le nom de la source depuis l'URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return "unknown"
    
    def _extract_published_date(self, item: Dict) -> Optional[str]:
        """Extrait la date de publication depuis les métadonnées"""
        try:
            # Recherche dans pagemap
            if 'pagemap' in item:
                pagemap = item['pagemap']
                
                # Métadonnées d'article de news
                if 'newsarticle' in pagemap:
                    news_article = pagemap['newsarticle'][0]
                    if 'datepublished' in news_article:
                        return news_article['datepublished']
                
                # Métadonnées générales
                if 'metatags' in pagemap:
                    metatags = pagemap['metatags'][0]
                    for key in ['article:published_time', 'og:updated_time', 'date']:
                        if key in metatags:
                            return metatags[key]
            
            return None
        except:
            return None
    
    def _calculate_relevance_score(self, item: Dict, search_type: GoogleSearchType) -> float:
        """Calcule un score de pertinence pour le résultat"""
        score = 0.0
        
        title = item.get('title', '').lower()
        snippet = item.get('snippet', '').lower()
        link = item.get('link', '').lower()
        
        # Bonus pour les sources fiables
        for source in self.financial_sources:
            if source.replace('www.', '') in link:
                score += 0.3
                break
        
        # Bonus pour les mots-clés pertinents
        keywords = {
            GoogleSearchType.MARKET_NEWS: ['market', 'trading', 'stock', 'financial'],
            GoogleSearchType.FINANCIAL_REPORTS: ['earnings', 'revenue', 'quarterly', 'annual'],
            GoogleSearchType.STOCK_ANALYSIS: ['analysis', 'target', 'price', 'rating'],
            GoogleSearchType.ECONOMIC_INDICATORS: ['gdp', 'inflation', 'employment', 'economic'],
            GoogleSearchType.CRYPTO_NEWS: ['bitcoin', 'crypto', 'blockchain', 'ethereum'],
            GoogleSearchType.FOREX_NEWS: ['forex', 'currency', 'exchange', 'dollar'],
            GoogleSearchType.COMMODITIES_NEWS: ['oil', 'gold', 'silver', 'commodity']
        }
        
        relevant_keywords = keywords.get(search_type, [])
        for keyword in relevant_keywords:
            if keyword in title:
                score += 0.2
            if keyword in snippet:
                score += 0.1
        
        # Bonus pour les contenus récents
        if 'today' in title or 'today' in snippet:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_daily_market_report(self, location: str = "global") -> MarketReport:
        """
        Génère un rapport de marché quotidien basé sur les recherches Google
        
        Args:
            location: Localisation pour la recherche (global, US, EU, etc.)
            
        Returns:
            Rapport de marché structuré
        """
        try:
            logger.info("📊 Génération rapport de marché quotidien")
            
            # Recherches multiples pour un rapport complet
            searches = [
                (GoogleSearchType.MARKET_NEWS, "market news today"),
                (GoogleSearchType.FINANCIAL_REPORTS, "earnings reports today"),
                (GoogleSearchType.ECONOMIC_INDICATORS, "economic indicators today"),
                (GoogleSearchType.STOCK_ANALYSIS, "market analysis today")
            ]
            
            all_results = []
            for search_type, query in searches:
                results = self.search_financial_markets(
                    query=query,
                    search_type=search_type,
                    max_results=5,
                    date_restrict="d1"
                )
                all_results.extend(results)
            
            # Tri par pertinence
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Génération du rapport
            report = self._generate_market_report(all_results, location)
            
            logger.info("✅ Rapport de marché généré")
            return report
            
        except Exception as e:
            logger.error(f"❌ Erreur génération rapport: {e}")
            return self._create_error_report(str(e))
    
    def get_daily_news_summary(self, categories: List[str] = None) -> List[DailyNewsItem]:
        """
        Récupère un résumé des nouvelles quotidiennes
        
        Args:
            categories: Catégories de nouvelles (market, crypto, forex, etc.)
            
        Returns:
            Liste des nouvelles importantes
        """
        try:
            logger.info("📰 Récupération nouvelles quotidiennes")
            
            if categories is None:
                categories = ['market', 'crypto', 'forex', 'commodities']
            
            news_items = []
            
            for category in categories:
                search_type = self._get_search_type_for_category(category)
                query = f"{category} news today"
                
                results = self.search_financial_markets(
                    query=query,
                    search_type=search_type,
                    max_results=3,
                    date_restrict="d1"
                )
                
                for result in results:
                    news_item = DailyNewsItem(
                        headline=result.title,
                        summary=result.snippet,
                        category=category,
                        source=result.source,
                        url=result.link,
                        published_date=result.published_date or "Unknown",
                        importance_level=self._assess_importance(result)
                    )
                    news_items.append(news_item)
            
            # Tri par importance
            news_items.sort(key=lambda x: self._importance_score(x.importance_level), reverse=True)
            
            logger.info(f"✅ {len(news_items)} nouvelles récupérées")
            return news_items
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération nouvelles: {e}")
            return []
    
    def _get_search_type_for_category(self, category: str) -> GoogleSearchType:
        """Mappe une catégorie vers un type de recherche"""
        mapping = {
            'market': GoogleSearchType.MARKET_NEWS,
            'crypto': GoogleSearchType.CRYPTO_NEWS,
            'forex': GoogleSearchType.FOREX_NEWS,
            'commodities': GoogleSearchType.COMMODITIES_NEWS,
            'stocks': GoogleSearchType.STOCK_ANALYSIS,
            'economic': GoogleSearchType.ECONOMIC_INDICATORS
        }
        return mapping.get(category, GoogleSearchType.MARKET_NEWS)
    
    def _assess_importance(self, result: GoogleSearchResult) -> str:
        """Évalue l'importance d'une nouvelle"""
        score = result.relevance_score
        
        if score >= 0.8:
            return "high"
        elif score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _importance_score(self, level: str) -> int:
        """Convertit le niveau d'importance en score numérique"""
        scores = {"high": 3, "medium": 2, "low": 1}
        return scores.get(level, 1)
    
    def _generate_market_report(self, results: List[GoogleSearchResult], location: str) -> MarketReport:
        """Génère un rapport de marché structuré"""
        
        # Analyse des résultats
        key_points = []
        sources = list(set([r.source for r in results]))
        sentiment = self._analyze_market_sentiment(results)
        impact = self._assess_market_impact(results)
        
        # Extraction des points clés
        for result in results[:5]:  # Top 5 résultats
            if result.relevance_score > 0.5:
                key_points.append(f"{result.title} ({result.source})")
        
        # Résumé basé sur les snippets
        summaries = [r.snippet for r in results[:3]]
        summary = " ".join(summaries)[:500] + "..." if len(summaries) > 0 else "Aucune information disponible"
        
        return MarketReport(
            title=f"Rapport de Marché Quotidien - {location.title()}",
            summary=summary,
            key_points=key_points,
            market_sentiment=sentiment,
            sources=sources,
            timestamp=datetime.now().isoformat(),
            market_impact=impact
        )
    
    def _analyze_market_sentiment(self, results: List[GoogleSearchResult]) -> str:
        """Analyse le sentiment du marché basé sur les résultats"""
        positive_words = ['gain', 'rise', 'up', 'positive', 'bullish', 'growth', 'profit']
        negative_words = ['fall', 'drop', 'down', 'negative', 'bearish', 'loss', 'decline']
        
        positive_count = 0
        negative_count = 0
        
        for result in results:
            text = f"{result.title} {result.snippet}".lower()
            
            for word in positive_words:
                if word in text:
                    positive_count += 1
            
            for word in negative_words:
                if word in text:
                    negative_count += 1
        
        if positive_count > negative_count:
            return "Bullish"
        elif negative_count > positive_count:
            return "Bearish"
        else:
            return "Neutral"
    
    def _assess_market_impact(self, results: List[GoogleSearchType]) -> str:
        """Évalue l'impact potentiel sur le marché"""
        high_impact_keywords = ['fed', 'federal reserve', 'interest rates', 'inflation', 'gdp']
        medium_impact_keywords = ['earnings', 'revenue', 'quarterly', 'annual']
        
        text = " ".join([f"{r.title} {r.snippet}" for r in results]).lower()
        
        for keyword in high_impact_keywords:
            if keyword in text:
                return "High"
        
        for keyword in medium_impact_keywords:
            if keyword in text:
                return "Medium"
        
        return "Low"
    
    def _create_error_report(self, error_message: str) -> MarketReport:
        """Crée un rapport d'erreur"""
        return MarketReport(
            title="Erreur - Rapport de Marché",
            summary=f"Erreur lors de la génération du rapport: {error_message}",
            key_points=["Erreur de connexion à l'API Google"],
            market_sentiment="Unknown",
            sources=["Error"],
            timestamp=datetime.now().isoformat(),
            market_impact="Unknown"
        )

def create_google_search_manager() -> Optional[GoogleSearchManager]:
    """
    Factory function pour créer une instance du gestionnaire Google Search
    
    Returns:
        Instance du gestionnaire ou None si configuration manquante
    """
    try:
        api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not api_key or not search_engine_id:
            logger.warning("⚠️ Configuration Google Search manquante")
            return None
        
        return GoogleSearchManager(api_key, search_engine_id)
        
    except Exception as e:
        logger.error(f"❌ Erreur création Google Search Manager: {e}")
        return None 