#!/usr/bin/env python3
"""
Intégration Google Custom Search Engine (CSE)
Utilise le moteur de recherche configuré par l'utilisateur
"""

import os
import requests
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class GoogleCSEResult:
    """Résultat de recherche Google CSE"""
    title: str
    link: str
    snippet: str
    source: str = "Google CSE"

@dataclass
class GoogleCSESearchResponse:
    """Réponse de recherche Google CSE"""
    results: List[GoogleCSEResult]
    total_results: int
    search_time: float
    query: str

class GoogleCSEIntegration:
    """Intégration Google Custom Search Engine"""
    
    def __init__(self):
        load_dotenv()
        # Utiliser les nouvelles variables d'environnement
        self.api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY') or os.getenv('GOOGLE_SEARCH_API_KEY')
        self.engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID') or "0426c6b27374b4a72"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key:
            print("⚠️ Clé API Google manquante. Configurez GOOGLE_CUSTOM_SEARCH_API_KEY dans .env")
    
    def search(self, query: str, num_results: int = 10, date_restrict: str = "d1") -> Optional[GoogleCSESearchResponse]:
        """Effectue une recherche avec Google CSE"""
        if not self.api_key:
            print("❌ Clé API manquante")
            return None
        
        params = {
            'key': self.api_key,
            'cx': self.engine_id,
            'q': query,
            'num': min(num_results, 10),  # Google CSE limite à 10 résultats par requête
            'dateRestrict': date_restrict
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraire les résultats
                items = data.get('items', [])
                results = []
                
                for item in items:
                    results.append(GoogleCSEResult(
                        title=item.get('title', ''),
                        link=item.get('link', ''),
                        snippet=item.get('snippet', '')
                    ))
                
                search_info = data.get('searchInformation', {})
                
                return GoogleCSESearchResponse(
                    results=results,
                    total_results=int(search_info.get('totalResults', 0)),
                    search_time=float(search_info.get('searchTime', 0)),
                    query=query
                )
            else:
                print(f"❌ Erreur API: {response.status_code}")
                print(f"📝 Réponse: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return None
    
    def search_stock_price(self, symbol: str) -> Optional[Dict]:
        """Recherche le prix d'une action"""
        query = f"{symbol} stock price today"
        response = self.search(query, num_results=5)
        
        if response and response.results:
            # Analyser les résultats pour extraire le prix
            for result in response.results:
                # Chercher des patterns de prix dans le snippet
                if any(keyword in result.snippet.lower() for keyword in ['$', 'price', 'stock', 'share']):
                    return {
                        'symbol': symbol,
                        'price': self._extract_price(result.snippet),
                        'source': result.link,
                        'confidence': 0.8,
                        'currency': 'USD'
                    }
        
        return None
    
    def search_market_news(self, keywords: List[str] = None) -> Optional[List[Dict]]:
        """Recherche des nouvelles du marché"""
        if not keywords:
            keywords = ['stock market', 'financial news', 'market update']
        
        news_items = []
        
        for keyword in keywords:
            query = f"{keyword} today"
            response = self.search(query, num_results=5)
            
            if response:
                for result in response.results:
                    news_items.append({
                        'title': result.title,
                        'content': result.snippet,
                        'url': result.link,
                        'source': result.source,
                        'category': keyword
                    })
        
        return news_items[:10]  # Limiter à 10 articles
    
    def search_market_briefing(self, location: str = "global") -> Optional[Dict]:
        """Recherche un briefing du marché"""
        query = f"{location} market briefing today financial news"
        response = self.search(query, num_results=5)
        
        if response and response.results:
            # Construire un briefing à partir des résultats
            briefing_content = ""
            sources = []
            
            for result in response.results:
                briefing_content += f"• {result.title}\n{result.snippet}\n\n"
                sources.append(result.link)
            
            return {
                'content': briefing_content.strip(),
                'sources': sources,
                'location': location,
                'timestamp': response.search_time
            }
        
        return None
    
    def _extract_price(self, text: str) -> Optional[str]:
        """Extrait un prix du texte"""
        import re
        
        # Patterns pour trouver des prix
        patterns = [
            r'\$(\d+\.?\d*)',  # $123.45
            r'(\d+\.?\d*)\s*USD',  # 123.45 USD
            r'price[:\s]*\$?(\d+\.?\d*)',  # price: $123.45
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_status(self) -> Dict:
        """Retourne le statut de l'intégration"""
        return {
            'status': 'operational' if self.api_key else 'missing_api_key',
            'engine_id': self.engine_id,
            'api_key_configured': bool(self.api_key),
            'base_url': self.base_url
        }

# Fonction de test
def test_google_cse_integration():
    """Test de l'intégration Google CSE"""
    print("🧪 Test Google CSE Integration")
    print("=" * 40)
    
    cse = GoogleCSEIntegration()
    status = cse.get_status()
    
    print(f"🔍 Engine ID: {status['engine_id']}")
    print(f"🔑 API Key: {'✅ Configurée' if status['api_key_configured'] else '❌ Manquante'}")
    print(f"📊 Status: {status['status']}")
    
    if status['api_key_configured']:
        # Test de recherche
        print("\n🔍 Test de recherche...")
        response = cse.search("AAPL stock price")
        
        if response:
            print(f"✅ Recherche réussie!")
            print(f"📊 Résultats trouvés: {response.total_results}")
            print(f"⏱️ Temps de recherche: {response.search_time}s")
            
            if response.results:
                print("\n📰 Premier résultat:")
                result = response.results[0]
                print(f"   Titre: {result.title}")
                print(f"   URL: {result.link}")
                print(f"   Snippet: {result.snippet[:100]}...")
        else:
            print("❌ Échec de la recherche")
    else:
        print("\n⚠️ Configurez GOOGLE_SEARCH_API_KEY dans .env")

if __name__ == "__main__":
    test_google_cse_integration() 