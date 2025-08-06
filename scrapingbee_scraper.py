import os
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement de manière sécurisée
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    logger.warning(f"⚠️ Impossible de charger .env: {e}")

@dataclass
class ScrapedData:
    url: str
    title: str
    content: str
    timestamp: datetime
    metadata: Dict

@dataclass
class ScrapingTask:
    id: str
    prompt: str
    status: str  # pending, processing, completed, failed
    results: Optional[Dict] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class ScrapingBeeScraper:
    def __init__(self):
        self.api_key = os.getenv('SCRAPINGBEE_API_KEY')
        self.base_url = "https://app.scrapingbee.com/api/v1"
        self.tasks = {}
        self._initialized = False
        
        if not self.api_key:
            logger.warning("⚠️ SCRAPINGBEE_API_KEY non configuré")
        
    def initialize_sync(self):
        """Initialisation synchrone du scraper"""
        try:
            if not self._initialized:
                if not self.api_key:
                    raise Exception("SCRAPINGBEE_API_KEY requis")
                
                self._initialized = True
                logger.info("✅ ScrapingBee Scraper initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation ScrapingBee: {e}")
            raise
    
    async def create_scraping_task(self, prompt: str, num_results: int = 5) -> str:
        """Crée une nouvelle tâche de scraping"""
        import uuid
        task_id = str(uuid.uuid4())
        
        task = ScrapingTask(
            id=task_id,
            prompt=prompt,
            status="pending",
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        logger.info(f"📋 Tâche de scraping créée: {task_id}")
        return task_id
    
    async def search_and_scrape(self, query: str, num_results: int = 5) -> List[ScrapedData]:
        """Recherche sur Google et scrape les résultats avec ScrapingBee"""
        if not self._initialized:
            await self.initialize()
        
        results = []
        
        try:
            logger.info(f"🔍 Recherche ScrapingBee: {query}")
            
            # Étape 1: Recherche Google avec ScrapingBee
            search_results = await self._search_google(query, num_results)
            
            if not search_results:
                logger.warning("⚠️ Aucun résultat de recherche trouvé")
                return results
            
            # Étape 2: Scraping des pages avec ScrapingBee
            for i, result in enumerate(search_results[:num_results]):
                try:
                    logger.info(f"📖 Scraping {i+1}/{len(search_results)}: {result['title']}")
                    
                    scraped_content = await self._scrape_page(result['url'])
                    
                    if scraped_content:
                        results.append(ScrapedData(
                            url=result['url'],
                            title=result['title'],
                            content=scraped_content,
                            timestamp=datetime.now(),
                            metadata={
                                'word_count': len(scraped_content.split()),
                                'language': 'fr',
                                'source': 'scrapingbee'
                            }
                        ))
                    
                except Exception as e:
                    logger.error(f"❌ Erreur scraping {result['url']}: {e}")
                    # Ajouter un résultat d'erreur
                    results.append(ScrapedData(
                        url=result['url'],
                        title=result['title'],
                        content=f"Erreur lors du scraping: {str(e)}",
                        timestamp=datetime.now(),
                        metadata={
                            'word_count': 10,
                            'language': 'fr',
                            'error': str(e)
                        }
                    ))
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche/scraping: {e}")
        
        return results
    
    async def _search_google(self, query: str, num_results: int = 5) -> List[Dict]:
        """Recherche sur des sites financiers directs avec ScrapingBee"""
        try:
            # Détecter si c'est une requête sur les marchés généraux ou une action spécifique
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['marché', 'marchés', 'financier', 'financiers', 'situation', 'aujourd\'hui', 'ia', 'ai', 'intelligence']):
                # Sites d'actualités financières pour les requêtes générales
                sites_financiers = [
                    {
                        'url': "https://www.reuters.com/markets/",
                        'title': "Reuters - Marchés financiers"
                    },
                    {
                        'url': "https://www.bloomberg.com/markets",
                        'title': "Bloomberg - Marchés"
                    },
                    {
                        'url': "https://www.ft.com/markets",
                        'title': "Financial Times - Marchés"
                    },
                    {
                        'url': "https://www.cnbc.com/markets/",
                        'title': "CNBC - Marchés"
                    },
                    {
                        'url': "https://www.marketwatch.com/",
                        'title': "MarketWatch - Actualités"
                    }
                ]
            else:
                # Sites de stocks pour les requêtes spécifiques
                stock_symbol = query.split()[0].upper()
                sites_financiers = [
                    {
                        'url': f"https://finance.yahoo.com/quote/{stock_symbol}",
                        'title': f"Yahoo Finance - {stock_symbol}"
                    },
                    {
                        'url': f"https://www.marketwatch.com/investing/stock/{stock_symbol.lower()}",
                        'title': f"MarketWatch - {stock_symbol}"
                    },
                    {
                        'url': f"https://www.reuters.com/companies/{stock_symbol}.O",
                        'title': f"Reuters - {stock_symbol}"
                    },
                    {
                        'url': f"https://www.bloomberg.com/quote/{stock_symbol}:US",
                        'title': f"Bloomberg - {stock_symbol}"
                    }
                ]
            
            logger.info(f"🔍 Recherche sur {min(len(sites_financiers), num_results)} sites financiers")
            
            # Retourner les sites financiers comme résultats de recherche
            return sites_financiers[:num_results]
                        
        except Exception as e:
            logger.error(f"❌ Erreur recherche sites financiers: {e}")
            return []  # Pas de fallback
    
    def _extract_links_from_html(self, html_content: str, query: str) -> List[Dict]:
        """Extrait les liens depuis le HTML de Google"""
        import re
        
        links = []
        
        # Patterns améliorés pour extraire les liens des résultats Google
        patterns = [
            # Pattern pour les résultats de recherche Google standard
            r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>',
            # Pattern pour les titres de résultats
            r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]*)</a></h3>',
            # Pattern pour les divs avec titres
            r'<div[^>]*class="[^"]*title[^"]*"[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]*)</a></div>',
            # Pattern pour les liens dans les résultats de recherche
            r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*"[^>]*>([^<]*)</a>',
            # Pattern générique pour tous les liens
            r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
        ]
        
        logger.info(f"🔍 Extraction de liens depuis {len(html_content)} caractères")
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            logger.info(f"🔍 Pattern {i+1}: {len(matches)} matches trouvés")
            
            for url, title in matches:
                logger.debug(f"🔍 Match trouvé: URL='{url[:100]}...' Title='{title[:100]}...'")
                
                # Nettoyer l'URL (enlever les paramètres Google)
                original_url = url
                if url.startswith('/url?q='):
                    url = url.split('/url?q=')[1].split('&')[0]
                elif url.startswith('/url?'):
                    url = url.split('/url?')[1].split('&')[0]
                
                logger.debug(f"🔍 URL nettoyée: {url[:100]}...")
                
                # Vérifier si c'est un lien valide
                is_valid = True
                reason = ""
                
                if not url.startswith('http'):
                    is_valid = False
                    reason = "Pas HTTP"
                elif url.startswith('https://www.google.com'):
                    is_valid = False
                    reason = "Google.com"
                elif url.startswith('https://accounts.google.com'):
                    is_valid = False
                    reason = "Accounts Google"
                elif url.startswith('https://maps.google.com'):
                    is_valid = False
                    reason = "Maps Google"
                elif url.startswith('https://support.google.com'):
                    is_valid = False
                    reason = "Support Google"
                elif len(title.strip()) <= 5:
                    is_valid = False
                    reason = "Titre trop court"
                elif any(domain in url.lower() for domain in ['google.com', 'youtube.com', 'facebook.com', 'instagram.com']):
                    is_valid = False
                    reason = "Domaine exclu"
                
                if is_valid:
                    # Nettoyer le titre
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    
                    if title and len(title) > 5:
                        links.append({
                            'url': url,
                            'title': title
                        })
                        logger.info(f"✅ Lien trouvé: {title[:50]}... -> {url}")
                    else:
                        logger.debug(f"❌ Titre invalide après nettoyage: '{title}'")
                else:
                    logger.debug(f"❌ Lien rejeté ({reason}): {url[:50]}...")
        
        # Supprimer les doublons
        seen_urls = set()
        unique_links = []
        for link in links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        logger.info(f"📄 Total: {len(unique_links)} liens uniques extraits")
        return unique_links
    

    
    async def _scrape_page(self, url: str) -> Optional[str]:
        """Scrape une page avec ScrapingBee"""
        try:
            # Paramètres ScrapingBee pour le scraping
            params = {
                'api_key': self.api_key,
                'url': url,
                'render_js': 'true',  # Rendu JS pour les pages dynamiques
                'premium_proxy': 'false',  # Proxy standard pour économiser les crédits
                'country_code': 'us'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        # ScrapingBee retourne du HTML, pas du JSON
                        html_content = await response.text()
                        
                        # Extraire le contenu du body
                        cleaned_content = self._extract_text_from_html(html_content)
                        logger.info(f"📄 Contenu extrait de {url}: {len(cleaned_content)} caractères.")
                        logger.debug(f"Contenu brut (aperçu): {cleaned_content[:500]}...")

                        return cleaned_content[:8000]  # Limite de caractères augmentée
                    else:
                        logger.error(f"❌ Erreur ScrapingBee scraping: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erreur scraping page {url}: {e}")
            return None
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extrait le texte du HTML"""
        if not html_content:
            return ""
        
        # Supprimer les balises script et style
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Extraire le texte des balises
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Nettoyer le texte
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)\-\$\%]', '', text)
        
        return text.strip()[:8000]
    
    def _clean_content(self, content: str) -> str:
        """Nettoie le contenu extrait"""
        if not content:
            return ""
        
        # Supprimer les espaces multiples
        content = re.sub(r'\s+', ' ', content)
        
        # Supprimer les caractères spéciaux
        content = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', content)
        
        # Limiter la longueur
        return content.strip()[:8000]
    
    async def process_with_llm(self, prompt: str, scraped_data: List[ScrapedData], market_snapshot: Dict) -> Dict:
        """Traite les données scrapées avec OpenAI"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Préparer le contexte
            context = self._prepare_context(scraped_data)
            logger.info(f"🧠 Contexte préparé pour OpenAI ({len(context)} caractères).")
            logger.debug(f"Contexte complet pour OpenAI: {context}")

            # Prompt système enrichi
            system_prompt = """Tu es un expert analyste financier de classe mondiale. Ta mission est de produire un rapport de marché EXHAUSTIF, DÉTAILLÉ et HAUTEMENT STRUCTURÉ. Combine les données factuelles (market_snapshot) avec l'analyse des textes (données collectées).

STRUCTURE OBLIGATOIRE DE LA RÉPONSE JSON :
{
    "market_snapshot": {
        "indices": {
            "S&P 500": {"price": 5447.87, "change": -8.55, "change_percent": -0.16},
            "NASDAQ": {"price": 17689.36, "change": -28.20, "change_percent": -0.16}
        },
        "commodities": {"Gold": {"price": 2330.20, "change": -1.20, "change_percent": -0.05}},
        "crypto": {"Bitcoin": {"price": 69304.58, "change": 450.15, "change_percent": 0.65}}
    },
    "summary": "Un résumé exécutif substantiel et approfondi. Intègre les données du snapshot pour contextualiser l'analyse. Minimum 500 mots.",
    "key_points": [
        "Point clé détaillé 1, intégrant une donnée factuelle si pertinent", 
        "...",
        "Point clé détaillé 10"
    ],
    "structured_data": {
        "market_sentiment": "Analyse du sentiment de marché (haussier, baissier, neutre) avec justification.",
        "key_trends": ["Tendance majeure 1 identifiée", "Tendance majeure 2", "..."],
        "major_events": ["Événement majeur 1 et son impact", "Événement majeur 2", "..."],
        "sector_analysis": "Analyse détaillée des secteurs mentionnés, en particulier l'IA."
    },
    "insights": ["Insight actionnable 1 basé sur une corrélation de données", "..."],
    "risks": ["Risque potentiel 1 avec explication", "..."],
    "opportunities": ["Opportunité d'investissement 1 avec justification", "..."],
    "sources_analysis": "Une brève critique de la fiabilité des sources textuelles fournies.",
    "confidence_score": 0.95,
    "sources": [{"title": "Titre de la source 1", "url": "URL de la source 1"}]
}"""
            
            logger.info("🤖 Appel à l'API OpenAI (gpt-4o) en cours pour une analyse exhaustive...")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Demande: {prompt}\n\nDONNÉES FACTUELLES (snapshot):\n{json.dumps(market_snapshot, indent=2)}\n\nDONNÉES COLLECTÉES (articles):\n{context}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=4000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement LLM: {e}")
            return {
                "summary": f"Erreur lors du traitement: {str(e)}",
                "key_points": [],
                "structured_data": {},
                "sources": [],
                "confidence_score": 0.0
            }
    
    def _prepare_context(self, scraped_data: List[ScrapedData]) -> str:
        """Prépare le contexte pour le LLM"""
        context_parts = []
        
        for idx, data in enumerate(scraped_data, 1):
            context_parts.append(f"""
Source {idx}: {data.title}
URL: {data.url}
Contenu: {data.content[:4000]}
---
""")
        
        return '\n'.join(context_parts)
    
    async def execute_scraping_task(self, task_id: str) -> Dict:
        """Exécute une tâche de scraping"""
        if task_id not in self.tasks:
            return {"error": "Tâche non trouvée"}
        
        task = self.tasks[task_id]
        task.status = "processing"
        
        try:
            logger.info(f"🚀 Début exécution tâche: {task_id}")
            
            # Scraping - Utiliser 3 sources pour un rapport plus complet
            scraped_data = await self.search_and_scrape(task.prompt, num_results=3)
            
            if not scraped_data:
                task.status = "failed"
                task.error = "Application non disponible - Aucune donnée trouvée"
                return {
                    "error": "Application non disponible",
                    "message": "Impossible de récupérer des données pour cette requête. Veuillez réessayer plus tard.",
                    "status": "unavailable"
                }
            
            # Étape 2: Récupérer les données factuelles de marché
            from stock_api_manager import stock_api_manager
            market_snapshot = stock_api_manager.get_market_snapshot()

            # Étape 3: Traitement LLM avec les données scrapées ET les données factuelles
            llm_result = await self.process_with_llm(task.prompt, scraped_data, market_snapshot)
            
            # Mettre à jour la tâche
            task.status = "completed"
            task.results = llm_result
            task.completed_at = datetime.now()
            
            logger.info(f"✅ Tâche {task_id} terminée avec succès")
            return llm_result
            
        except Exception as e:
            logger.error(f"❌ Erreur tâche {task_id}: {e}")
            task.status = "failed"
            task.error = str(e)
            return {
                "error": "Application non disponible",
                "message": f"Erreur technique: {str(e)}",
                "status": "error"
            }
    
    def get_task_status(self, task_id: str) -> Optional[ScrapingTask]:
        """Récupère le statut d'une tâche"""
        return self.tasks.get(task_id)
    
    async def initialize(self):
        """Initialisation asynchrone"""
        if not self._initialized:
            self.initialize_sync()
    
    def cleanup(self):
        """Nettoyage des ressources"""
        self.tasks.clear()
        self._initialized = False
        logger.info("🧹 ScrapingBee Scraper nettoyé")

# Fonction utilitaire pour obtenir le scraper
def get_scrapingbee_scraper():
    """Retourne une instance du ScrapingBee Scraper"""
    return ScrapingBeeScraper()

# Fonction de test
async def test_scrapingbee_scraper():
    """Test du ScrapingBee Scraper"""
    print("🧪 Test du ScrapingBee Scraper")
    print("=" * 50)
    
    scraper = get_scrapingbee_scraper()
    
    try:
        # Test d'initialisation
        scraper.initialize_sync()
        
        # Test de création de tâche
        print("📋 Test 1: Création de tâche")
        task_id = await scraper.create_scraping_task("Tesla stock price today latest news earnings", 3)
        print(f"✅ Tâche créée: {task_id}")
        
        # Test d'exécution
        print("🚀 Test 2: Exécution de la tâche")
        result = await scraper.execute_scraping_task(task_id)
        
        if "error" in result:
            print(f"❌ Erreur: {result['error']}")
        else:
            print("✅ Résultat obtenu:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(test_scrapingbee_scraper()) 