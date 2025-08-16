#!/usr/bin/env python3
"""
Google CSE comme source principale pour les données boursières
Intégration avec IA pour les rapports journaliers
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
class StockData:
    """Données boursières extraites"""
    symbol: str
    price: Optional[str]
    change: Optional[str]
    change_percent: Optional[str]
    volume: Optional[str]
    market_cap: Optional[str]
    source: str
    timestamp: datetime
    confidence: float

@dataclass
class MarketReport:
    """Rapport de marché généré par IA"""
    summary: str
    key_events: List[str]
    market_sentiment: str
    top_gainers: List[Dict]
    top_losers: List[Dict]
    sector_performance: Dict[str, str]
    recommendations: List[str]
    sources: List[str]
    generated_at: datetime

class GoogleCSEStockDataManager:
    """Gestionnaire de données boursières via Google CSE"""
    
    def __init__(self):
        load_dotenv()
        self.cse = GoogleCSEIntegration()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def get_stock_price(self, symbol: str) -> Optional[StockData]:
        """Récupère le prix d'une action via Google CSE"""
        query = f"{symbol} stock price real time"
        response = self.cse.search(query, num_results=5)
        
        if not response or not response.results:
            return None
        
        # Analyser les résultats pour extraire les données
        for result in response.results:
            stock_data = self._extract_stock_data(result.snippet, symbol)
            if stock_data:
                return stock_data
        
        return None
    
    def get_multiple_stock_prices(self, symbols: List[str]) -> Dict[str, StockData]:
        """Récupère les prix de plusieurs actions"""
        results = {}
        
        for symbol in symbols:
            stock_data = self.get_stock_price(symbol)
            if stock_data:
                results[symbol] = stock_data
        
        return results
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Vue d'ensemble du marché"""
        queries = [
            "stock market today overview",
            "market indices S&P 500 NASDAQ",
            "market sentiment today",
            "trading volume market activity"
        ]
        
        market_data = {}
        
        for query in queries:
            response = self.cse.search(query, num_results=3)
            if response and response.results:
                market_data[query] = [result.snippet for result in response.results]
        
        return market_data
    
    def generate_daily_report(self, symbols: List[str] = None) -> MarketReport:
        """Génère un rapport journalier avec l'IA"""
        print("📊 Génération du rapport journalier...")
        
        # Récupérer les données du marché
        market_overview = self.get_market_overview()
        
        # Récupérer les prix des actions principales
        if not symbols:
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX']
        
        stock_prices = self.get_multiple_stock_prices(symbols)
        
        # Préparer les données pour l'IA
        market_summary = self._prepare_market_summary(market_overview, stock_prices)
        
        # Générer le rapport avec l'IA
        ai_report = self._generate_ai_report(market_summary)
        
        return ai_report
    
    def _extract_stock_data(self, text: str, symbol: str) -> Optional[StockData]:
        """Extrait les données boursières du texte"""
        # Patterns pour extraire les prix
        price_patterns = [
            r'\$(\d+\.?\d*)',  # $123.45
            r'(\d+\.?\d*)\s*USD',  # 123.45 USD
            r'price[:\s]*\$?(\d+\.?\d*)',  # price: $123.45
        ]
        
        # Patterns pour les variations
        change_patterns = [
            r'(\+?\$?\d+\.?\d*)\s*\(([+-]?\d+\.?\d*%)\)',  # +$2.45 (+1.2%)
            r'([+-]?\d+\.?\d*%)\s*\(([+-]?\$?\d+\.?\d*)\)',  # +1.2% (+$2.45)
        ]
        
        price = None
        change = None
        change_percent = None
        
        # Extraire le prix
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price = match.group(1)
                break
        
        # Extraire les variations
        for pattern in change_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '$' in match.group(1):
                    change = match.group(1)
                    change_percent = match.group(2)
                else:
                    change_percent = match.group(1)
                    change = match.group(2)
                break
        
        if price:
            return StockData(
                symbol=symbol,
                price=price,
                change=change,
                change_percent=change_percent,
                volume=None,
                market_cap=None,
                source="Google CSE",
                timestamp=datetime.now(),
                confidence=0.8 if change else 0.6
            )
        
        return None
    
    def _prepare_market_summary(self, market_overview: Dict, stock_prices: Dict[str, StockData]) -> str:
        """Prépare un résumé pour l'IA"""
        summary = "Résumé du marché:\n\n"
        
        # Ajouter les données du marché
        for query, results in market_overview.items():
            summary += f"📊 {query}:\n"
            for result in results[:2]:
                summary += f"   - {result[:200]}...\n"
            summary += "\n"
        
        # Ajouter les prix des actions
        summary += "💰 Prix des actions principales:\n"
        for symbol, data in stock_prices.items():
            summary += f"   {symbol}: ${data.price}"
            if data.change:
                summary += f" ({data.change}, {data.change_percent})"
            summary += "\n"
        
        return summary
    
    def _generate_ai_report(self, market_summary: str) -> MarketReport:
        """Génère un rapport avec l'IA"""
        prompt = f"""
        En tant qu'analyste financier expert, génère un rapport journalier du marché basé sur ces informations:

        {market_summary}

        Génère un rapport structuré avec:
        1. Résumé exécutif (2-3 phrases)
        2. Événements clés du jour
        3. Sentiment du marché (hausse/baisse/neutre)
        4. Performances par secteur
        5. Recommandations d'investissement (2-3 points)

        Format JSON:
        {{
            "summary": "résumé exécutif",
            "key_events": ["événement 1", "événement 2"],
            "market_sentiment": "hausse/baisse/neutre",
            "top_gainers": [{{"symbol": "AAPL", "change": "+2.5%"}}],
            "top_losers": [{{"symbol": "TSLA", "change": "-1.8%"}}],
            "sector_performance": {{"tech": "+1.2%", "finance": "-0.5%"}},
            "recommendations": ["recommandation 1", "recommandation 2"]
        }}
        """
        
        try:
            from gpt5_compat import from_chat_completions_compat
            response = from_chat_completions_compat(
                client=self.openai_client,
                model=os.getenv("AI_MODEL", "gpt-5"),
                messages=[
                    {"role": "system", "content": "Tu es un analyste financier expert spécialisé dans les rapports de marché."},
                    {"role": "user", "content": prompt}
                ],
            )
            
            ai_response = response.choices[0].message.content
            
            # Parser la réponse JSON
            try:
                report_data = json.loads(ai_response)
            except:
                # Si le JSON n'est pas valide, créer un rapport basique
                report_data = {
                    "summary": "Rapport généré automatiquement",
                    "key_events": ["Analyse en cours"],
                    "market_sentiment": "neutre",
                    "top_gainers": [],
                    "top_losers": [],
                    "sector_performance": {},
                    "recommendations": ["Consulter un conseiller financier"]
                }
            
            return MarketReport(
                summary=report_data.get("summary", ""),
                key_events=report_data.get("key_events", []),
                market_sentiment=report_data.get("market_sentiment", "neutre"),
                top_gainers=report_data.get("top_gainers", []),
                top_losers=report_data.get("top_losers", []),
                sector_performance=report_data.get("sector_performance", {}),
                recommendations=report_data.get("recommendations", []),
                sources=["Google CSE", "OpenAI"],
                generated_at=datetime.now()
            )
            
        except Exception as e:
            print(f"❌ Erreur génération rapport IA: {e}")
            return MarketReport(
                summary="Erreur lors de la génération du rapport",
                key_events=[],
                market_sentiment="neutre",
                top_gainers=[],
                top_losers=[],
                sector_performance={},
                recommendations=["Vérifier la configuration"],
                sources=["Google CSE"],
                generated_at=datetime.now()
            )

# Fonction de test
def test_stock_data_manager():
    """Test du gestionnaire de données boursières"""
    print("🧪 Test Google CSE Stock Data Manager")
    print("=" * 50)
    
    manager = GoogleCSEStockDataManager()
    
    # Test 1: Prix d'une action
    print("\n💰 Test 1: Prix d'action AAPL")
    stock_data = manager.get_stock_price("AAPL")
    if stock_data:
        print(f"✅ {stock_data.symbol}: ${stock_data.price}")
        if stock_data.change:
            print(f"   Variation: {stock_data.change} ({stock_data.change_percent})")
    else:
        print("❌ Prix non trouvé")
    
    # Test 2: Vue d'ensemble du marché
    print("\n📊 Test 2: Vue d'ensemble du marché")
    market_overview = manager.get_market_overview()
    print(f"✅ {len(market_overview)} sources de données récupérées")
    
    # Test 3: Rapport journalier
    print("\n📈 Test 3: Rapport journalier")
    report = manager.generate_daily_report(['AAPL', 'GOOGL', 'MSFT'])
    print(f"✅ Rapport généré: {report.summary[:100]}...")
    print(f"   Sentiment: {report.market_sentiment}")
    print(f"   Événements: {len(report.key_events)}")
    print(f"   Recommandations: {len(report.recommendations)}")

if __name__ == "__main__":
    test_stock_data_manager() 