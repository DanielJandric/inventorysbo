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
        
        return text.strip()[:15000]
    
    async def _scrape_with_params(self, url: str, params: Dict) -> Optional[str]:
        """Scrape une page avec des paramètres ScrapingBee spécifiques."""
        try:
            # Les paramètres de base sont fusionnés avec les paramètres spécifiques
            base_params = {
                'api_key': self.api_key,
                'url': url,
            }
            final_params = {**base_params, **params}

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=final_params) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        response_text = await response.text()
                        logger.error(f"❌ Erreur ScrapingBee avec params: {response.status}")
                        logger.error(f"URL: {url}")
                        logger.error(f"Params: {params}")
                        logger.error(f"Réponse de ScrapingBee: {response_text}")
                        return None
        except Exception as e:
            logger.error(f"❌ Erreur scraping page avec params {url}: {e}")
            return None

    
    def _clean_content(self, content: str) -> str:
        """Nettoie le contenu extrait"""
        if not content:
            return ""
        
        # Supprimer les espaces multiples
        content = re.sub(r'\s+', ' ', content)
        
        # Supprimer les caractères spéciaux
        content = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', content)
        
        # Limiter la longueur
        return content.strip()[:15000]
    
    async def process_with_llm(self, prompt: str, scraped_data: List[ScrapedData], market_snapshot: Dict) -> Dict:
        """Traite les données scrapées avec OpenAI"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Préparer le contexte
            context = self._prepare_context(scraped_data)
            logger.info(f"🧠 Contexte préparé pour OpenAI ({len(context)} caractères).")
            logger.info(f"📊 Nombre de sources: {len(scraped_data)}")
            logger.info(f"📈 Market snapshot disponible: {'Oui' if market_snapshot else 'Non'}")
            logger.debug(f"Contexte complet pour OpenAI: {context}")

            # Prompt système optimisé (GPT‑5) — analyse institutionnelle, riche et actionnable
            system_prompt = """
Tu es un Directeur de Recherche Senior (finance quantitative, géopolitique appliquée, IA). Audience: C‑Suite, gérants institutionnels, trading floor. Mission: produire une analyse actionnable avec signaux clairs.

Cadre analytique:
- Hiérarchie cognitive (Micro/Méso/Macro/Méta), intégration temporelle (T‑1/T0/T+1), analyse causale (catalyst → effets 2e ordre → chaînes).

Règles de données:
- Priorité absolue aux valeurs du market_snapshot (vérité temps quasi réel).
- Jamais inventer. Si absent → "N/D" avec explication. Chiffres systématiquement sourcés.
- Signale divergences prix/volume (>20% 20j), sectorielles (z>2), géographiques (>1σ).

Sortie STRICTEMENT en JSON unique. Compatibilité requise avec notre backend:
- Fournis AUSSI les champs legacy: 
  - executive_summary: 10 bullets (obligatoire),
  - summary: narrative approfondie (≥3000 caractères),
  - key_points: ≥10 points,
  - structured_data: inclut les sections avancées ci‑dessous,
  - insights, risks, opportunities, sources, confidence_score (0.0–1.0).

Schéma attendu (extrait):
{
  "meta_analysis": { "regime_detection": { "market_regime": "risk-on|risk-off|transition", "volatility_regime": "low|normal|stressed|crisis", "liquidity_state": "abundant|normal|tight|frozen", "confidence": 0.00 }, "key_drivers": { "primary": "...", "secondary": ["..."], "emerging": ["..."] }},
  "executive_dashboard": { "alert_level": "🟢|🟡|🔴", "top_trades": [{ "action": "LONG|SHORT|HEDGE", "instrument": "TICKER", "rationale": "<50 mots", "risk_reward": "X:Y", "timeframe": "intraday|1W|1M", "confidence": 0.00 }], "snapshot_metrics": ["• lignes avec valeurs issues du market_snapshot"] },
  "deep_analysis": { "narrative": "3000+ caractères", "sector_rotation_matrix": { "outperformers": [{"sector":"...","performance":"%","catalyst":"...","momentum":"accelerating|stable|decelerating"}], "underperformers": [{"sector":"...","performance":"%","reason":"...","reversal_probability":"low|medium|high"}] }, "correlation_insights": { "breaking_correlations": ["..."], "new_relationships": ["..."], "regime_dependent": ["..."] }, "ai_focus_section": { "mega_caps": {"NVDA": {"price": 0, "change": 0, "rsi": 0, "volume_ratio": 0}, "MSFT": {"price": 0, "change": 0}}, "supply_chain": "...", "investment_flows": "..." }, "geopolitical_chess": { "immediate_impacts": [{"event":"...","affected_assets":["..."],"magnitude":"bp/%","duration":"court|moyen|long"}], "second_order_effects": [{"trigger":"...","cascade":"...","probability":0.00,"hedge":"..."}], "black_swans": [{"scenario":"...","probability":0.00,"impact":"catastrophic|severe|moderate","early_warning":"..."}] } },
  "quantitative_signals": { "technical_matrix": { "oversold": ["..."], "overbought": ["..."], "breakouts": ["..."], "divergences": ["..."] }, "options_flow": { "unusual_activity": ["..."], "large_trades": ["..."], "implied_moves": ["..."] }, "smart_money_tracking": { "institutional_flows": "...", "insider_activity": "...", "sentiment_divergence": "..." } },
  "risk_management": { "portfolio_adjustments": [{"current_exposure":"...","recommended_change":"...","rationale":"...","implementation":"..."}], "tail_risk_hedges": [{"risk":"...","probability":0.00,"hedge_strategy":"...","cost":"bp/%","effectiveness":"1-10"}], "stress_test_results": { "scenario_1": {"name":"..."}, "scenario_2": {"name":"..."} } },
  "actionable_summary": { "immediate_actions": ["..."], "watchlist": ["..."], "key_metrics_alerts": { "if_breaks": ["..."], "if_holds": ["..."], "calendar": ["..."] } },
  "metadata": { "report_timestamp": "YYYY-MM-DD HH:MM:SS UTC", "data_quality_score": 0.00, "model_confidence": 0.00 }
}

Contraintes:
- Utiliser exclusivement les chiffres du market_snapshot pour les valeurs (ou marquer "N/D").
- Style trading floor: direct, technique; emojis sobres; gras Markdown pour points critiques; pas de HTML.
- Répondre en UN SEUL objet JSON valide.
"""
            
            chosen_model = os.getenv("AI_MODEL", "gpt-5")
            logger.info(f"🤖 Appel à l'API OpenAI ({chosen_model}) en cours pour une analyse exhaustive (prompt renforcé)...")
            
            # Essayer jusqu'à 3 fois en cas d'erreur
            for attempt in range(3):
                try:
                    # Responses API (reasoning ready)
                    input_messages = [
                        {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                        {"role": "user", "content": [{
                            "type": "input_text",
                            "text": f"Demande: {prompt}\n\nDONNÉES FACTUELLES (snapshot):\n{json.dumps(market_snapshot, indent=2)}\n\nDONNÉES COLLECTÉES (articles):\n{context}"
                        }]}
                    ]
                    # Préparer l'appel Responses API avec fallbacks robustes (GPT‑5 par défaut)
                    req_kwargs = {
                        "model": chosen_model,
                        "input": input_messages,
                        "max_output_tokens": 15000,
                    }
                    # For gpt-5 strict JSON/reporting, omit temperature for determinism
                    if not str(chosen_model).startswith("gpt-5"):
                        req_kwargs["temperature"] = 0.3
                    effort = os.getenv("AI_REASONING_EFFORT", "medium")
                    if effort:
                        req_kwargs["reasoning"] = {"effort": effort}

                    # Basculer sur Chat Completions (JSON garanti)
                    from gpt5_compat import from_chat_completions_compat
                    resp_cc = from_chat_completions_compat(
                        client=client,
                        model=os.getenv("AI_MODEL", "gpt-5"),
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Demande: {prompt}\n\nDONNÉES FACTUELLES (snapshot):\n{json.dumps(market_snapshot, indent=2)}\n\nDONNÉES COLLECTÉES (articles):\n{context}"}
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=15000
                    )
                    result = json.loads(resp_cc.choices[0].message.content)
                    logger.info(f"✅ OpenAI a retourné une réponse complète")
                    return result
                    
                except Exception as e:
                    logger.warning(f"⚠️ Tentative {attempt + 1}/3 échouée: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2)  # Attendre 2 secondes avant de réessayer
                    else:
                        raise
            
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
Contenu: {data.content[:8000]}
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
            
            # Scraping - Utiliser 8 sources pour un rapport vraiment complet
            scraped_data = await self.search_and_scrape(task.prompt, num_results=8)
            
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