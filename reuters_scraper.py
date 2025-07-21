import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReutersScraper:
    """
    Scraper pour récupérer les données financières depuis Reuters.com et NZZ.ch
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # URLs Reuters pour différents marchés
        self.urls = {
            'indices': {
                'S&P 500': 'https://www.reuters.com/markets/indices',
                'NASDAQ': 'https://www.reuters.com/markets/indices',
                'Dow Jones': 'https://www.reuters.com/markets/indices',
                'CAC 40': 'https://www.reuters.com/markets/indices',
                'DAX': 'https://www.reuters.com/markets/indices',
                'SMI': 'https://www.reuters.com/markets/indices'
            },
            'crypto': {
                'Bitcoin': 'https://www.reuters.com/markets/currencies',
                'Ethereum': 'https://www.reuters.com/markets/currencies'
            },
            'bonds': {
                'US 10Y': 'https://www.reuters.com/markets/rates-bonds',
                'Bund 10Y': 'https://www.reuters.com/markets/rates-bonds'
            }
        }
        
        # URLs NZZ pour les actualités suisses
        self.nzz_urls = [
            'https://www.nzz.ch/wirtschaft',      # Économie
            'https://www.nzz.ch/finanzen',        # Finances
            'https://www.nzz.ch/unternehmen',     # Entreprises
            'https://www.nzz.ch/international',   # International
            'https://www.nzz.ch/schweiz',         # Suisse
            'https://www.nzz.ch/meinung'          # Opinions/Éditoriaux
        ]
        
        # URLs AP News pour les actualités internationales
        self.ap_urls = [
            'https://apnews.com/business',        # Business
            'https://apnews.com/politics',        # Politique
            'https://apnews.com/technology',      # Technologie
            'https://apnews.com/science',         # Science
            'https://apnews.com/health'           # Santé
        ]
    
    def get_market_data(self) -> Dict[str, str]:
        """
        Récupère toutes les données de marché depuis Reuters
        """
        logger.info("🔍 Début du scraping Reuters...")
        
        market_data = {}
        
        try:
            # Scraper les indices
            indices_data = self._scrape_indices()
            market_data.update(indices_data)
            
            # Pause pour éviter d'être détecté
            time.sleep(random.uniform(1, 3))
            
            # Scraper les crypto
            crypto_data = self._scrape_crypto()
            market_data.update(crypto_data)
            
            # Pause
            time.sleep(random.uniform(1, 3))
            
            # Scraper les obligations
            bonds_data = self._scrape_bonds()
            market_data.update(bonds_data)
            
            # Si aucune donnée récupérée, essayer des sources alternatives
            if not market_data:
                logger.warning("⚠️ Aucune donnée de marché récupérée, essai sources alternatives...")
                alternative_data = self._get_alternative_market_data()
                market_data.update(alternative_data)
            
            logger.info(f"✅ Scraping terminé - {len(market_data)} données récupérées")
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du scraping: {e}")
            return {}
    
    def _scrape_indices(self) -> Dict[str, str]:
        """
        Scrape les indices boursiers
        """
        logger.info("📊 Scraping des indices...")
        
        try:
            url = "https://www.reuters.com/markets/indices"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher les données des indices dans la page
            indices_data = {}
            
            # Recherche des éléments contenant les données d'indices
            # (à adapter selon la structure HTML de Reuters)
            index_elements = soup.find_all(['div', 'span'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['index', 'market', 'price', 'quote']))
            
            for element in index_elements:
                text = element.get_text().strip()
                if any(index in text for index in ['S&P', 'NASDAQ', 'Dow', 'CAC', 'DAX', 'SMI']):
                    logger.info(f"Trouvé: {text}")
                    # Extraire le nom et la valeur
                    # (logique à affiner selon le format exact)
            
            return indices_data
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping indices: {e}")
            return {}
    
    def _scrape_crypto(self) -> Dict[str, str]:
        """
        Scrape les crypto-monnaies
        """
        logger.info("🪙 Scraping des crypto...")
        
        try:
            url = "https://www.reuters.com/markets/currencies"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Logique similaire pour les crypto
            crypto_data = {}
            
            return crypto_data
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping crypto: {e}")
            return {}
    
    def _scrape_bonds(self) -> Dict[str, str]:
        """
        Scrape les obligations
        """
        logger.info("📈 Scraping des obligations...")
        
        try:
            url = "https://www.reuters.com/markets/rates-bonds"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Logique similaire pour les obligations
            bonds_data = {}
            
            return bonds_data
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping obligations: {e}")
            return {}
    
    def get_financial_news(self, max_news: int = 5) -> List[Dict[str, str]]:
        """
        Scrape les actualités financières depuis Reuters, NZZ et AP News
        """
        logger.info("📰 Scraping des actualités financières...")
        
        news_list = []
        
        # Scraper Reuters
        reuters_news = self._scrape_reuters_news(max_news // 3)
        news_list.extend(reuters_news)
        
        # Scraper NZZ
        nzz_news = self._scrape_nzz_news(max_news // 3)
        news_list.extend(nzz_news)
        
        # Scraper AP News
        ap_news = self._scrape_ap_news(max_news // 3)
        news_list.extend(ap_news)
        
        # Si aucune actualité récupérée, essayer des sources alternatives
        if not news_list:
            logger.warning("⚠️ Aucune actualité récupérée, essai sources alternatives...")
            alternative_news = self._scrape_alternative_sources(max_news)
            news_list.extend(alternative_news)
        
        logger.info(f"✅ {len(news_list)} actualités récupérées (Reuters: {len(reuters_news)}, NZZ: {len(nzz_news)}, AP: {len(ap_news)})")
        return news_list[:max_news]
    
    def _scrape_reuters_news(self, max_news: int) -> List[Dict[str, str]]:
        """
        Scrape les actualités depuis Reuters
        """
        logger.info("📰 Scraping Reuters...")
        
        news_list = []
        
        try:
            # URLs des sections d'actualités élargies
            news_urls = [
                "https://www.reuters.com/markets/finance/",
                "https://www.reuters.com/markets/",
                "https://www.reuters.com/business/",
                "https://www.reuters.com/technology/",
                "https://www.reuters.com/politics/",
                "https://www.reuters.com/world/",
                "https://www.reuters.com/companies/",
                "https://www.reuters.com/economy/"
            ]
            
            for url in news_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Chercher les articles d'actualités
                    articles = soup.find_all(['article', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['article', 'story', 'news', 'headline']))
                    
                    for article in articles[:max_news//len(news_urls)]:  # Répartir les articles entre les sections
                        # Extraire le titre
                        title_element = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
                        if title_element:
                            title = title_element.get_text().strip()
                            
                            # Extraire le résumé/description
                            summary_element = article.find(['p', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['summary', 'description', 'excerpt']))
                            summary = summary_element.get_text().strip() if summary_element else ""
                            
                            # Extraire l'URL
                            link_element = article.find('a')
                            url = link_element.get('href') if link_element else ""
                            if url and not url.startswith('http'):
                                url = f"https://www.reuters.com{url}"
                            
                            if title and len(title) > 10:  # Filtrer les titres trop courts
                                news_list.append({
                                    'title': title,
                                    'summary': summary,
                                    'url': url,
                                    'source': 'Reuters'
                                })
                    
                    # Pause entre les requêtes
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.error(f"❌ Erreur scraping news depuis {url}: {e}")
                    continue
            
            logger.info(f"✅ {len(news_list)} actualités récupérées")
            return news_list[:max_news]  # Garder le max demandé
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping Reuters: {e}")
            return []
    
    def _scrape_nzz_news(self, max_news: int) -> List[Dict[str, str]]:
        """
        Scrape les actualités depuis NZZ.ch
        """
        logger.info("📰 Scraping NZZ...")
        
        news_list = []
        
        try:
            for url in self.nzz_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Chercher les articles NZZ (structure spécifique)
                    articles = soup.find_all(['article', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['article', 'story', 'news', 'headline', 'teaser']))
                    
                    for article in articles[:max_news//len(self.nzz_urls)]:
                        # Extraire le titre
                        title_element = article.find(['h1', 'h2', 'h3', 'h4', 'a', 'h5'])
                        if title_element:
                            title = title_element.get_text().strip()
                            
                            # Extraire le résumé/description
                            summary_element = article.find(['p', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['summary', 'description', 'excerpt', 'teaser']))
                            summary = summary_element.get_text().strip() if summary_element else ""
                            
                            # Extraire l'URL
                            link_element = article.find('a')
                            article_url = link_element.get('href') if link_element else ""
                            if article_url and not article_url.startswith('http'):
                                article_url = f"https://www.nzz.ch{article_url}"
                            
                            if title and len(title) > 10:  # Filtrer les titres trop courts
                                news_list.append({
                                    'title': title,
                                    'summary': summary,
                                    'url': article_url,
                                    'source': 'NZZ'
                                })
                    
                    # Pause entre les requêtes
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.error(f"❌ Erreur scraping NZZ depuis {url}: {e}")
                    continue
            
            return news_list[:max_news]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping NZZ: {e}")
            return []
    
    def _scrape_ap_news(self, max_news: int) -> List[Dict[str, str]]:
        """
        Scrape les actualités depuis AP News
        """
        logger.info("📰 Scraping AP News...")
        
        news_list = []
        
        try:
            for url in self.ap_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Chercher les articles AP News (structure spécifique)
                    articles = soup.find_all(['article', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['article', 'story', 'news', 'headline', 'card', 'teaser']))
                    
                    for article in articles[:max_news//len(self.ap_urls)]:
                        # Extraire le titre
                        title_element = article.find(['h1', 'h2', 'h3', 'h4', 'a', 'h5'])
                        if title_element:
                            title = title_element.get_text().strip()
                            
                            # Extraire le résumé/description
                            summary_element = article.find(['p', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['summary', 'description', 'excerpt', 'teaser', 'lede']))
                            summary = summary_element.get_text().strip() if summary_element else ""
                            
                            # Extraire l'URL
                            link_element = article.find('a')
                            article_url = link_element.get('href') if link_element else ""
                            if article_url and not article_url.startswith('http'):
                                article_url = f"https://apnews.com{article_url}"
                            
                            if title and len(title) > 10:  # Filtrer les titres trop courts
                                news_list.append({
                                    'title': title,
                                    'summary': summary,
                                    'url': article_url,
                                    'source': 'AP News'
                                })
                    
                    # Pause entre les requêtes
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.error(f"❌ Erreur scraping AP News depuis {url}: {e}")
                    continue
            
            return news_list[:max_news]
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping AP News: {e}")
            return []
    
    def _scrape_alternative_sources(self, max_news: int) -> List[Dict[str, str]]:
        """
        Scrape des sources alternatives si les principales échouent
        """
        logger.info("📰 Scraping sources alternatives...")
        
        news_list = []
        
        # Sources alternatives plus simples
        alternative_urls = [
            'https://www.bloomberg.com/markets',
            'https://www.ft.com/markets',
            'https://www.cnbc.com/markets/'
        ]
        
        for url in alternative_urls:
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Chercher les titres d'articles
                articles = soup.find_all(['h1', 'h2', 'h3', 'h4'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['headline', 'title', 'story']))
                
                for article in articles[:max_news//len(alternative_urls)]:
                    title = article.get_text().strip()
                    
                    if title and len(title) > 10:
                        news_list.append({
                            'title': title,
                            'summary': "",
                            'url': url,
                            'source': 'Alternative'
                        })
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"❌ Erreur scraping alternative {url}: {e}")
                continue
        
        return news_list[:max_news]
    
    def _get_alternative_market_data(self) -> Dict[str, str]:
        """
        Récupère des données de marché depuis des sources alternatives
        """
        logger.info("📊 Récupération données alternatives...")
        
        market_data = {}
        
        try:
            # Utiliser Yahoo Finance comme fallback
            import yfinance as yf
            
            symbols = {
                'S&P 500': '^GSPC',
                'NASDAQ': '^IXIC', 
                'Dow Jones': '^DJI',
                'Bitcoin': 'BTC-USD',
                'Ethereum': 'ETH-USD'
            }
            
            for name, symbol in symbols.items():
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    if 'currentPrice' in info and info['currentPrice']:
                        price = info['currentPrice']
                        change = info.get('regularMarketChange', 0)
                        change_percent = info.get('regularMarketChangePercent', 0)
                        market_data[name] = f"${price:.2f} ({change:+.2f}, {change_percent:+.2f}%)"
                    
                except Exception as e:
                    logger.error(f"❌ Erreur Yahoo Finance {name}: {e}")
                    continue
            
            return market_data
            
        except ImportError:
            logger.error("❌ Yahoo Finance non disponible")
            return {}
        except Exception as e:
            logger.error(f"❌ Erreur données alternatives: {e}")
            return {}
    
    def format_market_data(self, data: Dict[str, str]) -> str:
        """
        Formate les données pour le prompt Gemini
        """
        if not data:
            return "Aucune donnée disponible via Reuters"
        
        formatted_lines = []
        for name, value in data.items():
            formatted_lines.append(f"{name}: {value}")
        
        return "\n".join(formatted_lines)
    
    def format_news_data(self, news_list: List[Dict[str, str]]) -> str:
        """
        Formate les actualités pour le prompt Gemini avec liens
        """
        if not news_list:
            return "Aucune actualité disponible"
        
        formatted_lines = ["ACTUALITÉS RÉCENTES (Reuters + NZZ + AP News):"]
        
        # Catégoriser les actualités par mots-clés
        categories = {
            'FINANCE': [],
            'TECHNOLOGIE': [],
            'POLITIQUE': [],
            'ÉCONOMIE': [],
            'MONDE': [],
            'ENTREPRISES': []
        }
        
        for news in news_list:
            title_lower = news['title'].lower()
            
            if any(word in title_lower for word in ['bank', 'finance', 'market', 'trading', 'stock', 'bond', 'crypto']):
                categories['FINANCE'].append(news)
            elif any(word in title_lower for word in ['tech', 'ai', 'artificial intelligence', 'software', 'digital', 'cyber']):
                categories['TECHNOLOGIE'].append(news)
            elif any(word in title_lower for word in ['politic', 'election', 'government', 'congress', 'parliament']):
                categories['POLITIQUE'].append(news)
            elif any(word in title_lower for word in ['economy', 'gdp', 'inflation', 'interest rate', 'fed', 'ecb']):
                categories['ÉCONOMIE'].append(news)
            elif any(word in title_lower for word in ['china', 'russia', 'ukraine', 'europe', 'asia', 'middle east']):
                categories['MONDE'].append(news)
            else:
                categories['ENTREPRISES'].append(news)
        
        # Formater par catégorie avec liens
        for category, articles in categories.items():
            if articles:
                formatted_lines.append(f"\n📰 {category}:")
                for i, news in enumerate(articles, 1):
                    source_tag = f"[{news['source']}]" if 'source' in news else ""
                    url_tag = f"({news['url']})" if news.get('url') else ""
                    formatted_lines.append(f"   {i}. {news['title']} {source_tag}")
                    if news['summary']:
                        formatted_lines.append(f"      {news['summary'][:100]}...")
                    if url_tag:
                        formatted_lines.append(f"      Lien: {url_tag}")
        
        return "\n".join(formatted_lines)

def test_reuters_scraper():
    """
    Test du scraper Reuters
    """
    scraper = ReutersScraper()
    
    print("🧪 Test du scraper Reuters...")
    print("=" * 50)
    
    # Test de connexion
    try:
        response = scraper.session.get("https://www.reuters.com", timeout=5)
        print(f"✅ Connexion Reuters: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return
    
    # Test du scraping des données de marché
    print("\n📊 Test des données de marché...")
    market_data = scraper.get_market_data()
    
    if market_data:
        for name, value in market_data.items():
            print(f"{name}: {value}")
    else:
        print("Aucune donnée de marché récupérée")
    
    # Test du scraping des actualités
    print("\n📰 Test des actualités financières...")
    news_data = scraper.get_financial_news(max_news=3)
    
    if news_data:
        for i, news in enumerate(news_data, 1):
            print(f"{i}. {news['title']}")
            if news['summary']:
                print(f"   {news['summary']}")
            print()
    else:
        print("Aucune actualité récupérée")
    
    # Format pour Gemini
    print("\n📝 Format complet pour Gemini:")
    print("=" * 40)
    
    market_formatted = scraper.format_market_data(market_data)
    news_formatted = scraper.format_news_data(news_data)
    
    print("DONNÉES DE MARCHÉ:")
    print(market_formatted)
    print("\n" + "="*40 + "\n")
    print(news_formatted)

if __name__ == "__main__":
    test_reuters_scraper() 