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
from datetime import timedelta

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
                    details = await self._scrape_page_with_metadata(result['url'])
                    if details and details.get('text'):
                        text = details['text']
                        published_at = details.get('published_at') or datetime.now()
                        results.append(ScrapedData(
                            url=result['url'],
                            title=result['title'],
                            content=text,
                            timestamp=published_at,
                            metadata={
                                'word_count': len(text.split()),
                                'language': 'fr',
                                'source': 'scrapingbee',
                                'scraped_at': datetime.now().isoformat(),
                                'published_at_raw': details.get('published_at_raw')
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
            
            # Filtrer: conserver uniquement les articles publiés dans les dernières 24h, puis trier (récents d'abord)
            try:
                now_ts = datetime.now().timestamp()
                def _is_recent(dt: Optional[datetime]) -> bool:
                    try:
                        if not dt:
                            return False
                        return (now_ts - dt.timestamp()) <= 24 * 3600
                    except Exception:
                        return False
                results = [r for r in results if _is_recent(r.timestamp)]
                results.sort(key=lambda x: (x.timestamp or datetime.min), reverse=True)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"❌ Erreur recherche/scraping: {e}")
        
        return results

    async def search_x_recent(self, topic_query: str, max_items: int = 6, max_age_hours: int = 2) -> List[ScrapedData]:
        """Scrape X (Twitter) search results for recent posts on a topic.

        - Uses ScrapingBee with JS rendering to load X search page
        - Parses tweets' text and ISO timestamps from <time datetime="...">
        - Filters to items within the last `max_age_hours` hours
        """
        items: List[ScrapedData] = []
        try:
            if not self._initialized:
                await self.initialize()

            # Build X search URL for live (latest) posts, restrict to FR/EN via query keywords
            q = quote_plus(topic_query)
            url = f"https://x.com/search?q={q}&f=live"

            params = {
                'api_key': self.api_key,
                'url': url,
                'render_js': 'true',
                'premium_proxy': 'false',
                'country_code': 'us'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status != 200:
                        logger.warning(f"⚠️ X search status {resp.status} pour {topic_query}")
                        return items
                    html = await resp.text()

            try:
                from bs4 import BeautifulSoup  # type: ignore
            except Exception:
                logger.warning("⚠️ BeautifulSoup non disponible, impossible de parser X.com")
                return items

            soup = BeautifulSoup(html or '', 'lxml')
            now = datetime.now()
            candidates = []
            # Tweets sont souvent dans <article role="article">
            for art in soup.find_all('article'):
                try:
                    # timestamp
                    t = art.find('time')
                    iso = t.get('datetime') if t else None
                    ts = None
                    if iso:
                        try:
                            ts = datetime.fromisoformat(iso.replace('Z', '+00:00'))
                        except Exception:
                            ts = None
                    # content
                    # concaténer les textes
                    text_parts = [n.get_text(' ', strip=True) for n in art.find_all('div')]
                    raw_text = ' '.join([p for p in text_parts if p]).strip()
                    # heuristique pour nettoyer
                    content = self._clean_content(raw_text)[:800]
                    if not content:
                        continue
                    # link
                    status_link = None
                    for a in art.find_all('a'):
                        href = a.get('href') or ''
                        if '/status/' in href:
                            status_link = f"https://x.com{href}"
                            break
                    candidates.append((ts, content, status_link))
                except Exception:
                    continue

            # Filtrer par recence: <= max_age_hours
            max_age = timedelta(hours=max_age_hours)
            filtered = []
            for ts, content, link in candidates:
                if ts is None:
                    continue
                try:
                    age = now - ts
                    if age <= max_age:
                        filtered.append((ts, content, link))
                except Exception:
                    continue

            # trier recent d'abord, limiter
            filtered.sort(key=lambda x: x[0], reverse=True)
            for ts, content, link in filtered[:max_items]:
                items.append(ScrapedData(
                    url=link or url,
                    title=f"X.com: {topic_query[:40]}",
                    content=content,
                    timestamp=ts,
                    metadata={
                        'source': 'x.com',
                        'topic': topic_query,
                        'language': 'und',
                        'word_count': len(content.split()),
                    }
                ))
        except Exception as e:
            logger.error(f"❌ Erreur X.com scraping: {e}")
        return items
    
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

    async def _scrape_page_with_metadata(self, url: str) -> Optional[Dict]:
        """Scrape une page et renvoie le texte + date de publication si détectable."""
        try:
            params = {
                'api_key': self.api_key,
                'url': url,
                'render_js': 'true',
                'premium_proxy': 'false',
                'country_code': 'us'
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"❌ Erreur ScrapingBee scraping: {response.status}")
                        return None
                    html_content = await response.text()
                    cleaned_content = self._extract_text_from_html(html_content)
                    # Extraire published_at depuis HTML ou headers
                    published_at, raw = self._extract_published_time(html_content, dict(response.headers))
                    return {
                        'text': cleaned_content[:8000],
                        'published_at': published_at,
                        'published_at_raw': raw
                    }
        except Exception as e:
            logger.error(f"❌ Erreur scraping page (with metadata) {url}: {e}")
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

    def _parse_datetime_str(self, s: str) -> Optional[datetime]:
        try:
            st = s.strip()
            if not st:
                return None
            # ISO 8601 simple
            st = st.replace('Z', '+00:00')
            try:
                return datetime.fromisoformat(st)
            except Exception:
                pass
            # RFC 2822 (headers)
            try:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(st)
            except Exception:
                return None
        except Exception:
            return None

    def _extract_published_time(self, html_content: str, headers: Optional[Dict] = None) -> (Optional[datetime], Optional[str]):
        """Extrait la date de publication depuis le HTML ou les en-têtes HTTP."""
        raw = None
        try:
            from bs4 import BeautifulSoup  # type: ignore
            soup = BeautifulSoup(html_content or '', 'lxml')
            # Meta tags courants
            candidates = []
            for selector, attr in [
                (('meta', {'property': 'article:published_time'}), 'content'),
                (('meta', {'name': 'article:published_time'}), 'content'),
                (('meta', {'property': 'og:published_time'}), 'content'),
                (('meta', {'property': 'og:updated_time'}), 'content'),
                (('meta', {'itemprop': 'datePublished'}), 'content'),
                (('meta', {'name': 'date'}), 'content'),
                (('time', {'datetime': True}), 'datetime'),
            ]:
                try:
                    tag = soup.find(*selector)
                    if tag and tag.get(attr):
                        candidates.append(tag.get(attr))
                except Exception:
                    continue
            for c in candidates:
                dt = self._parse_datetime_str(c)
                if dt:
                    return dt, c
        except Exception:
            pass
        try:
            # Headers HTTP
            if headers:
                for key in ['last-modified', 'date']:
                    hv = headers.get(key) or headers.get(key.title())
                    if hv:
                        dt = self._parse_datetime_str(hv)
                        if dt:
                            return dt, hv
        except Exception:
            pass
        return None, raw
    
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

            # Prompt système optimisé (GPT‑5) — verbosité/raisonnement renforcés, géopolitique à jour, indicateurs extraits du scrap
            system_prompt = """
Tu es un Directeur de Recherche Senior (finance quantitative, géopolitique appliquée, IA). Audience: C‑Suite, gérants institutionnels, trading floor. Mission: produire une analyse EXHAUSTIVE, TRÈS DÉTAILLÉE et rigoureusement argumentée. Ne sois pas permissif ni paresseux.

Cadre analytique:
- Hiérarchie cognitive (Micro/Méso/Macro/Méta), intégration temporelle (T‑1/T0/T+1), analyse causale (catalyst → effets 2e ordre → chaînes).
- Explicite les mécanismes de transmission, indicateurs menant/retardés, et conditions de rupture de régime.

Règles de données:
- Priorité absolue aux valeurs du market_snapshot (vérité temps quasi réel).
- Exploite STRICTEMENT les articles scrappés (contexte fourni) et privilégie les nouvelles récentes (≤ 48–72h; <24h si dispo). Ignore les extrapolations non sourcées.
- Jamais inventer. Si absent → "N/D" avec explication. Chiffres systématiquement sourcés (titre+URL) quand issus du scrap.
- Signale divergences prix/volume (>20% 20j), sectorielles (z>2), géographiques (>1σ).

Sortie STRICTEMENT en JSON unique. Compatibilité requise avec notre backend:
- Fournis AUSSI les champs legacy: 
  - executive_summary: 10 bullets (obligatoire, denses et actionnables),
  - summary: narrative approfondie (≥4000 caractères) avec raisonnement structuré,
  - key_points: ≥12 points à haut signal,
  - structured_data: inclut les sections avancées ci‑dessous,
  - insights, risks, opportunities, sources, confidence_score (0.0–1.0).

Schéma attendu (extrait):
{
  "meta_analysis": { "regime_detection": { "market_regime": "risk-on|risk-off|transition", "volatility_regime": "low|normal|stressed|crisis", "liquidity_state": "abundant|normal|tight|frozen", "confidence": 0.00 }, "key_drivers": { "primary": "...", "secondary": ["..."], "emerging": ["..."] }},
  "executive_dashboard": { "alert_level": "🟢|🟡|🔴", "top_trades": [{ "action": "LONG|SHORT|HEDGE", "instrument": "TICKER", "rationale": "<50 mots", "risk_reward": "X:Y", "timeframe": "intraday|1W|1M", "confidence": 0.00 }], "snapshot_metrics": ["• lignes avec valeurs issues du market_snapshot"] },
  "deep_analysis": { "narrative": "4000+ caractères", "sector_rotation_matrix": { "outperformers": [{"sector":"...","performance":"%","catalyst":"...","momentum":"accelerating|stable|decelerating"}], "underperformers": [{"sector":"...","performance":"%","reason":"...","reversal_probability":"low|medium|high"}] }, "correlation_insights": { "breaking_correlations": ["..."], "new_relationships": ["..."], "regime_dependent": ["..."] }, "ai_focus_section": { "mega_caps": {"NVDA": {"price": 0, "change": 0, "rsi": 0, "volume_ratio": 0}, "MSFT": {"price": 0, "change": 0}}, "supply_chain": "...", "investment_flows": "..." }, "geopolitical_chess": { "immediate_impacts": [{"event":"(événement géopolitique précis, daté ≤72h)","affected_assets":["..."],"magnitude":"bp/%","duration":"court|moyen|long","sources":[{"title":"...","url":"..."}]}], "second_order_effects": [{"trigger":"...","cascade":"...","probability":0.00,"hedge":"..."}], "black_swans": [{"scenario":"...","probability":0.00,"impact":"catastrophic|severe|moderate","early_warning":"..."}] } },
  "quantitative_signals": { "technical_matrix": { "oversold": ["..."], "overbought": ["..."], "breakouts": ["..."], "divergences": ["..."] }, "options_flow": { "unusual_activity": ["..."], "large_trades": ["..."], "implied_moves": ["..."] }, "smart_money_tracking": { "institutional_flows": "...", "insider_activity": "...", "sentiment_divergence": "..." } },
  "risk_management": { "portfolio_adjustments": [{"current_exposure":"...","recommended_change":"...","rationale":"...","implementation":"..."}], "tail_risk_hedges": [{"risk":"...","probability":0.00,"hedge_strategy":"...","cost":"bp/%","effectiveness":"1-10"}], "stress_test_results": { "scenario_1": {"name":"..."}, "scenario_2": {"name":"..."} } },
  "actionable_summary": { "immediate_actions": ["..."], "watchlist": ["..."], "key_metrics_alerts": { "if_breaks": ["..."], "if_holds": ["..."], "calendar": ["..."] } },
  "economic_indicators": { "inflation": {"US": "<valeur%>", "EU": "<valeur%>"}, "central_banks": ["Fed <taux%>", "BCE <taux%>"], "gdp_growth": {"US": "<valeur%>", "China": "<valeur%>"}, "unemployment": {"US": "<valeur%>", "EU": "<valeur%>"}, "additional_indicators": [{"name":"PMI Manufacturing US","value":"<valeur>","period":"<mois>","source":"<titre>"}] },
  "metadata": { "report_timestamp": "YYYY-MM-DD HH:MM:SS UTC", "data_quality_score": 0.00, "model_confidence": 0.00 }
}

Exigences géopolitiques (obligatoire):
- Analyse à jour issue des DERNIÈRES nouvelles scrappées (≤72h); si plusieurs versions d’un même événement, privilégie la plus récente et cite la source.
- Détaille causes → effets de 2e ordre → risques de queue; propose hedges concrets.

Exigences indicateurs (obligatoire):
- Extrait les indicateurs explicitement mentionnés dans les articles (CPI/PPI, Core CPI/PCE, PMI/ISM, NFP/chômage, retail sales, GDP/GDPNow, Fed/BCE/BoE/BoJ, VIX…).
- Renseigne le bloc economic_indicators ci‑dessus avec des valeurs lisibles (unités et période implicites via le texte) quand disponibles; sinon "N/D".

Contraintes générales:
- Utiliser exclusivement les chiffres du market_snapshot pour les prix/variations; compléter avec le scrap pour le narratif et les indicateurs macro.
- Style trading floor: direct, technique; gras Markdown pour points critiques; pas de HTML.
- Emojis sobres et professionnels pour signaler tendances/risques/insights: 📈/📉 (tendances), 🟢/🟡/🔴 (régime/alerte), ⚠️ (risque), 💡 (insight), 🏦 (banques centrales), 🌍 (macro/géo), ⏱️ (temporalité), 📊 (métriques). Fréquence: 1–2 par section max; jamais dans les nombres ou clés JSON.
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

                    # Utiliser exclusivement Responses API (JSON garanti)
                    from gpt5_compat import from_responses_simple, extract_output_text
                    resp = from_responses_simple(
                        client=client,
                        model=os.getenv("AI_MODEL", "gpt-5"),
                        messages=[
                            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                            {"role": "user", "content": [{"type": "input_text", "text": f"Demande: {prompt}\n\nDONNÉES FACTUELLES (snapshot):\n{json.dumps(market_snapshot, indent=2)}\n\nDONNÉES COLLECTÉES (articles):\n{context}"}]}
                        ],
                        max_output_tokens=15000,
                        reasoning_effort=os.getenv("AI_REASONING_EFFORT", "medium")
                    )
                    raw = extract_output_text(resp) or ""

                    # Parsing JSON robuste (tolère ```json fences, guillemets typographiques, texte avant/après)
                    def _safe_parse_json(text: str):
                        try:
                            s = (text or "").strip()
                            # retirer les fences ```json ... ``` si présents
                            s = re.sub(r"```\s*json\s*", "", s, flags=re.IGNORECASE)
                            s = s.replace('```', '').strip()
                            # normaliser guillemets typographiques
                            trans = {ord('\u201c'): '"', ord('\u201d'): '"', ord('\u2019'): "'", ord('\u2013'): '-', ord('\u2014'): '-'}
                            s = s.translate(trans)
                            # tentative directe
                            try:
                                return json.loads(s)
                            except Exception:
                                pass
                            # extraire un objet JSON équilibré naïvement
                            depth = 0
                            start_idx = None
                            for i, ch in enumerate(s):
                                if ch == '{':
                                    if depth == 0:
                                        start_idx = i
                                    depth += 1
                                elif ch == '}' and depth > 0:
                                    depth -= 1
                                    if depth == 0 and start_idx is not None:
                                        candidate = s[start_idx:i+1]
                                        try:
                                            return json.loads(candidate)
                                        except Exception:
                                            start_idx = None
                                            continue
                            return None
                        except Exception:
                            return None

                    parsed = _safe_parse_json(raw)
                    if parsed is None:
                        # fallback structuré au lieu d'échouer (évite retry inutile)
                        parsed = {
                            "summary": raw[:10000],
                            "key_points": [],
                            "structured_data": {},
                            "insights": [],
                            "risks": [],
                            "opportunities": [],
                            "sources": [],
                            "confidence_score": 0.0,
                        }

                    result = parsed
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
            
            # Scraping - Utiliser 8 sources (sites financiers)
            scraped_data = await self.search_and_scrape(task.prompt, num_results=8)

            # Ajouter X.com (tweets récents ≤2h) sur la même thématique
            try:
                x_items = await self.search_x_recent(task.prompt, max_items=6, max_age_hours=2)
                if x_items:
                    # Préfixer pour priorité aux signaux temps réel
                    scraped_data = x_items + scraped_data
            except Exception as _ex:
                logger.warning(f"⚠️ X.com indisponible: {_ex}")
            
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