#!/usr/bin/env python3
"""
Version améliorée de l'intégration Google CSE + IA OpenAI pour les rapports de marché
"""
import os
import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_cse_integration import GoogleCSEIntegration
from openai import OpenAI

@dataclass
class EnhancedMarketData:
    """Données de marché enrichies"""
    market_summary: str
    stock_prices: Dict[str, Dict]
    market_news: List[str]
    sector_data: Dict[str, str]
    economic_indicators: Dict[str, str]
    sources: List[str]

@dataclass
class EnhancedMarketReport:
    """Rapport de marché enrichi par IA"""
    summary: str
    key_events: List[str]
    market_sentiment: str
    top_gainers: List[Dict]
    top_losers: List[Dict]
    sector_performance: Dict[str, str]
    recommendations: List[str]
    economic_analysis: str
    risk_assessment: str
    sources: List[str]
    generated_at: datetime

class EnhancedGoogleCSEAIReport:
    """Gestionnaire amélioré pour rapports de marché avec Google CSE + IA"""
    
    def __init__(self):
        load_dotenv()
        self.cse = GoogleCSEIntegration()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def get_comprehensive_market_data(self) -> EnhancedMarketData:
        """Récupère des données de marché complètes via Google CSE"""
        print("🔍 Collecte de données de marché via Google CSE...")
        
        # Recherches spécifiques pour différents aspects du marché
        search_queries = {
            "market_overview": [
                "stock market today overview",
                "market indices S&P 500 NASDAQ Dow Jones",
                "market sentiment today",
                "trading volume market activity"
            ],
            "stock_prices": [
                "AAPL stock price today",
                "GOOGL stock price today", 
                "MSFT stock price today",
                "TSLA stock price today",
                "AMZN stock price today",
                "META stock price today",
                "NVDA stock price today"
            ],
            "market_news": [
                "stock market news today",
                "market headlines today",
                "financial news breaking",
                "earnings reports today"
            ],
            "sector_performance": [
                "technology sector performance today",
                "financial sector performance today",
                "healthcare sector performance today",
                "energy sector performance today"
            ],
            "economic_indicators": [
                "inflation data today",
                "interest rates Federal Reserve",
                "unemployment data",
                "GDP growth economic indicators"
            ]
        }
        
        market_data = {}
        
        # Collecter les données pour chaque catégorie
        for category, queries in search_queries.items():
            market_data[category] = {}
            for query in queries:
                response = self.cse.search(query, num_results=3)
                if response and response.results:
                    market_data[category][query] = [
                        {
                            'title': result.title,
                            'snippet': result.snippet,
                            'url': result.link
                        }
                        for result in response.results
                    ]
        
        # Extraire les prix d'actions
        stock_prices = {}
        for query in search_queries["stock_prices"]:
            symbol = query.split()[0]  # Extraire le symbole
            response = self.cse.search(query, num_results=2)
            if response and response.results:
                price_data = self._extract_price_from_results(response.results, symbol)
                if price_data:
                    stock_prices[symbol] = price_data
        
        # Préparer les données enrichies
        return EnhancedMarketData(
            market_summary=self._create_market_summary(market_data),
            stock_prices=stock_prices,
            market_news=self._extract_news_headlines(market_data.get("market_news", {})),
            sector_data=self._extract_sector_data(market_data.get("sector_performance", {})),
            economic_indicators=self._extract_economic_data(market_data.get("economic_indicators", {})),
            sources=["Google CSE"]
        )
    
    def generate_enhanced_ai_report(self, symbols: List[str] = None) -> EnhancedMarketReport:
        """Génère un rapport enrichi avec l'IA basé sur Google CSE"""
        print("📊 Génération du rapport enrichi avec IA...")
        
        # Récupérer les données de marché
        market_data = self.get_comprehensive_market_data()
        
        # Préparer le prompt pour l'IA
        ai_prompt = self._create_enhanced_ai_prompt(market_data, symbols)
        
        # Générer le rapport avec l'IA
        ai_report = self._generate_ai_report(ai_prompt)
        
        return ai_report
    
    def _extract_price_from_results(self, results: List, symbol: str) -> Optional[Dict]:
        """Extrait les prix des résultats Google CSE"""
        for result in results:
            # Patterns pour extraire les prix
            price_patterns = [
                rf'\${symbol}\s*\$?(\d+\.?\d*)',
                rf'{symbol}\s*\$?(\d+\.?\d*)',
                r'\$(\d+\.?\d*)\s*per\s*share',
                r'trading\s+at\s*\$(\d+\.?\d*)',
                r'current\s+price\s*\$(\d+\.?\d*)'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, result.snippet, re.IGNORECASE)
                if match:
                    return {
                        'price': match.group(1),
                        'source': result.title,
                        'url': result.link,
                        'snippet': result.snippet[:100]
                    }
        return None
    
    def _create_market_summary(self, market_data: Dict) -> str:
        """Crée un résumé du marché"""
        summary = "📊 RÉSUMÉ DU MARCHÉ (Google CSE)\n\n"
        
        # Ajouter les données de marché
        if "market_overview" in market_data:
            summary += "🎯 VUE D'ENSEMBLE:\n"
            for query, results in market_data["market_overview"].items():
                if results:
                    summary += f"   • {query}: {results[0]['snippet'][:150]}...\n"
            summary += "\n"
        
        # Ajouter les prix d'actions
        if "stock_prices" in market_data:
            summary += "💰 PRIX D'ACTIONS:\n"
            for query, results in market_data["stock_prices"].items():
                if results:
                    symbol = query.split()[0]
                    summary += f"   • {symbol}: {results[0]['snippet'][:100]}...\n"
            summary += "\n"
        
        return summary
    
    def _extract_news_headlines(self, news_data: Dict) -> List[str]:
        """Extrait les titres de nouvelles"""
        headlines = []
        for query, results in news_data.items():
            for result in results:
                headlines.append(f"{result['title']}: {result['snippet'][:100]}...")
        return headlines[:10]  # Limiter à 10 nouvelles
    
    def _extract_sector_data(self, sector_data: Dict) -> Dict[str, str]:
        """Extrait les données sectorielles"""
        sectors = {}
        for query, results in sector_data.items():
            if results:
                sector_name = query.split()[0].capitalize()
                sectors[sector_name] = results[0]['snippet'][:100]
        return sectors
    
    def _extract_economic_data(self, economic_data: Dict) -> Dict[str, str]:
        """Extrait les indicateurs économiques"""
        indicators = {}
        for query, results in economic_data.items():
            if results:
                indicator_name = query.split()[0].capitalize()
                indicators[indicator_name] = results[0]['snippet'][:100]
        return indicators
    
    def _create_enhanced_ai_prompt(self, market_data: EnhancedMarketData, symbols: List[str] = None) -> str:
        """Crée un prompt enrichi pour l'IA"""
        
        prompt = f"""
Tu es un analyste financier expert spécialisé dans les rapports de marché. 
Génère un rapport journalier complet basé sur les données Google CSE suivantes:

{market_data.market_summary}

📰 NOUVELLES DU MARCHÉ:
{chr(10).join([f"• {news}" for news in market_data.market_news[:5]])}

📈 PERFORMANCES SECTORIELLES:
{chr(10).join([f"• {sector}: {data}" for sector, data in market_data.sector_data.items()])}

📊 INDICATEURS ÉCONOMIQUES:
{chr(10).join([f"• {indicator}: {data}" for indicator, data in market_data.economic_indicators.items()])}

💰 PRIX D'ACTIONS PRINCIPALES:
{chr(10).join([f"• {symbol}: ${data['price']} ({data['source']})" for symbol, data in market_data.stock_prices.items()])}

Génère un rapport structuré au format JSON avec:
1. Résumé exécutif (3-4 phrases)
2. Événements clés du jour (liste)
3. Sentiment du marché (hausse/baisse/neutre avec pourcentage)
4. Top gagnants et perdants
5. Analyse sectorielle
6. Recommandations d'investissement (3-4 points)
7. Évaluation des risques
8. Analyse économique

Format JSON:
{{
    "summary": "résumé exécutif détaillé",
    "key_events": ["événement 1", "événement 2", "événement 3"],
    "market_sentiment": "hausse/baisse/neutre avec pourcentage",
    "top_gainers": [{{"symbol": "AAPL", "change": "+2.5%", "reason": "raison"}}],
    "top_losers": [{{"symbol": "TSLA", "change": "-1.8%", "reason": "raison"}}],
    "sector_performance": {{"tech": "+1.2%", "finance": "-0.5%", "healthcare": "+0.8%"}},
    "recommendations": ["recommandation 1", "recommandation 2", "recommandation 3"],
    "risk_assessment": "évaluation des risques actuels",
    "economic_analysis": "analyse économique du jour"
}}
"""
        return prompt
    
    def _generate_ai_report(self, prompt: str) -> EnhancedMarketReport:
        """Génère le rapport avec l'IA"""
        try:
            import os
            from gpt5_compat import from_chat_completions_compat
            response = from_chat_completions_compat(
                client=self.openai_client,
                model=os.getenv("AI_MODEL", "gpt-5"),
                messages=[
                    {"role": "system", "content": "Tu es un analyste financier expert avec 20 ans d'expérience. Tu utilises Google CSE comme source principale pour tes analyses."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
            # Parser la réponse JSON
            try:
                report_data = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback si le JSON n'est pas valide
                report_data = {
                    "summary": "Rapport généré avec Google CSE et IA",
                    "key_events": ["Analyse en cours"],
                    "market_sentiment": "neutre",
                    "top_gainers": [],
                    "top_losers": [],
                    "sector_performance": {},
                    "recommendations": ["Consulter un conseiller financier"],
                    "risk_assessment": "Évaluation en cours",
                    "economic_analysis": "Analyse économique en cours"
                }
            
            return EnhancedMarketReport(
                summary=report_data.get("summary", ""),
                key_events=report_data.get("key_events", []),
                market_sentiment=report_data.get("market_sentiment", "neutre"),
                top_gainers=report_data.get("top_gainers", []),
                top_losers=report_data.get("top_losers", []),
                sector_performance=report_data.get("sector_performance", {}),
                recommendations=report_data.get("recommendations", []),
                economic_analysis=report_data.get("economic_analysis", ""),
                risk_assessment=report_data.get("risk_assessment", ""),
                sources=["Google CSE", "OpenAI GPT-4"],
                generated_at=datetime.now()
            )
            
        except Exception as e:
            print(f"❌ Erreur génération rapport IA: {e}")
            return EnhancedMarketReport(
                summary="Erreur lors de la génération du rapport",
                key_events=[],
                market_sentiment="neutre",
                top_gainers=[],
                top_losers=[],
                sector_performance={},
                recommendations=["Vérifier la configuration"],
                economic_analysis="Analyse non disponible",
                risk_assessment="Évaluation non disponible",
                sources=["Google CSE"],
                generated_at=datetime.now()
            )

def test_enhanced_report():
    """Test du rapport enrichi"""
    print("🧪 Test Rapport Enrichi Google CSE + IA")
    print("=" * 60)
    
    manager = EnhancedGoogleCSEAIReport()
    
    # Test du rapport enrichi
    print("\n📊 Génération du rapport enrichi...")
    report = manager.generate_enhanced_ai_report(['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
    
    print(f"\n✅ Rapport généré:")
    print(f"   📝 Résumé: {report.summary[:200]}...")
    print(f"   📈 Sentiment: {report.market_sentiment}")
    print(f"   📰 Événements: {len(report.key_events)}")
    print(f"   💰 Gagnants: {len(report.top_gainers)}")
    print(f"   📉 Perdants: {len(report.top_losers)}")
    print(f"   🎯 Recommandations: {len(report.recommendations)}")
    print(f"   ⚠️ Risques: {report.risk_assessment[:100]}...")
    print(f"   📊 Analyse économique: {report.economic_analysis[:100]}...")
    print(f"   🔗 Sources: {', '.join(report.sources)}")

if __name__ == "__main__":
    test_enhanced_report() 