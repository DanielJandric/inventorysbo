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
from datetime import timezone

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG
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

    async def search_and_scrape_deep(self, topic_query: str, per_site: int = 12, max_age_hours: int = 72, min_chars: int = 25000) -> List[ScrapedData]:
        """Scrape en profondeur uniquement Yahoo Finance, MarketWatch et CNN, en retenant les articles récents.

        - Sites: finance.yahoo.com, marketwatch.com, cnn.com (world/business)
        - Filtre: published_at dans les dernières max_age_hours
        - Objectif: total contenu >= min_chars (sinon tente d'élargir le nombre de liens)
        """
        if not self._initialized:
            await self.initialize()

        def _now_utc() -> datetime:
            try:
                return datetime.now(timezone.utc)
            except Exception:
                # Fallback naïf
                return datetime.utcnow().replace(tzinfo=None)

        def _normalize_ts(dt_obj: Optional[datetime]) -> Optional[datetime]:
            if not dt_obj:
                return None
            try:
                if dt_obj.tzinfo is None:
                    return dt_obj.replace(tzinfo=timezone.utc)
                return dt_obj.astimezone(timezone.utc)
            except Exception:
                return dt_obj

        def _is_recent_dt(dt: Optional[datetime]) -> bool:
            try:
                if not dt:
                    return False
                dtz = _normalize_ts(dt)
                # Force timezone-aware UTC for both sides to avoid naive/aware comparisons
                if dtz and dtz.tzinfo is None:
                    dtz = dtz.replace(tzinfo=timezone.utc)
                nowz = _now_utc()
                if nowz.tzinfo is None:
                    nowz = nowz.replace(tzinfo=timezone.utc)
                return (nowz - dtz) <= timedelta(hours=max_age_hours)
            except Exception:
                return False

        async def _gather_domain(domain: str, start_urls: List[str], link_predicate, max_links: int) -> List[str]:
            links: List[str] = []
            seen: set = set()
            for start in start_urls:
                try:
                    html = await self._scrape_with_params(start, {
                        'render_js': 'false',
                        'premium_proxy': 'true',
                        'block_resources': 'true',
                        'wait': '1200',
                        'country_code': 'us',
                    })
                    if not html:
                        continue
                    from bs4 import BeautifulSoup  # type: ignore
                    soup = BeautifulSoup(html or '', 'lxml')
                    for a in soup.find_all('a'):
                        href = a.get('href') or ''
                        if not href:
                            continue
                        if href.startswith('/'):
                            href = f"https://{domain}{href}"
                        if (domain in href) and link_predicate(href) and href not in seen:
                            seen.add(href)
                            links.append(href)
                        if len(links) >= max_links:
                            break
                except Exception:
                    continue
                if len(links) >= max_links:
                    break
            return links

        # Heuristiques de liens d'articles par domaine
        def _is_mw_article(url: str) -> bool:
            u = url.lower()
            return ('marketwatch.com' in u) and ('/story/' in u or '/press-release/' not in u) and ('/videos/' not in u)
        def _is_cnn_article(url: str) -> bool:
            u = url.lower()
            return ('cnn.com' in u) and ('/world/' in u or '/business/' in u) and ('/live-news/' not in u)

        # Points d'entrée par site
        marketwatch_starts = [
            'https://www.marketwatch.com/',
            'https://www.marketwatch.com/markets',
            'https://www.marketwatch.com/economy-politics',
        ]
        cnn_starts = [
            'https://www.cnn.com/world',
            'https://www.cnn.com/business',
        ]

        # RSS helpers (contournent headers trop longs et anti‑bot JS)
        async def _fetch_rss_items(feeds: List[str], source_name: str, max_items: int) -> List[ScrapedData]:
            items: List[ScrapedData] = []
            try:
                import xml.etree.ElementTree as ET  # lightweight
            except Exception:
                return items
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36'
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                for f in feeds:
                    try:
                        # Essai direct avec timeout court
                        text = None
                        try:
                            async with session.get(f, timeout=10) as resp:
                                if resp.status == 200:
                                    text = await resp.text()
                                    logger.info(f"📰 RSS direct réussi: {f} ({len(text)} chars)")
                        except Exception as e:
                            logger.debug(f"📰 RSS direct échoué {f}: {e}")
                        
                        # Fallback via ScrapingBee proxy (sans JS) si clé API disponible
                        if not text and self.api_key and self.api_key != 'test_key_for_testing':
                            try:
                                async with session.get(self.base_url, params={
                                    'api_key': self.api_key,
                                    'url': f,
                                    'render_js': 'false'
                                }, timeout=15) as r2:
                                    if r2.status == 200:
                                        text = await r2.text()
                                        logger.info(f"📰 RSS via ScrapingBee: {f}")
                            except Exception as e:
                                logger.debug(f"📰 RSS ScrapingBee échoué {f}: {e}")
                        
                        if not text:
                            logger.warning(f"⚠️ Impossible de récupérer RSS: {f}")
                            continue
                        
                        try:
                            root = ET.fromstring(text)
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur parsing XML {f}: {e}")
                            continue
                        
                        # RSS 2.0: channel/item
                        for item in root.findall('.//item'):
                            try:
                                link_el = item.find('link')
                                title_el = item.find('title')
                                desc_el = item.find('description')
                                pub_el = item.find('pubDate')
                                
                                link = (link_el.text or '').strip() if link_el is not None else ''
                                title = (title_el.text or '').strip() if title_el is not None else link[:120]
                                desc = (desc_el.text or '').strip() if desc_el is not None else ''
                                ts = self._parse_datetime_str(pub_el.text) if pub_el is not None else None
                                ts = _normalize_ts(ts)
                                
                                # Debug logging
                                logger.debug(f"📰 RSS item: link='{link[:50]}...', title='{title[:50]}...', desc_len={len(desc)}, ts={ts}")
                                
                                if not link:
                                    logger.debug("⚠️ RSS item ignoré: pas de lien")
                                    continue
                                
                                # Pour RSS, être plus permissif sur la date (articles jusqu'à 7 jours)
                                if ts and (_now_utc() - ts) > timedelta(days=7):
                                    logger.debug(f"📰 Article trop ancien ignoré: {title[:50]}... ({ts})")
                                    continue
                                
                                # Content depuis description (fallback)
                                items.append(ScrapedData(
                                    url=link,
                                    title=title[:120],
                                    content=desc[:4000] if desc else title[:200],  # Fallback sur titre si pas de description
                                    timestamp=ts or datetime.now(),
                                    metadata={'source': source_name, 'from': 'rss'}
                                ))
                                logger.info(f"📰 Article RSS ajouté: {title[:60]}... ({source_name}) - {len(desc)} chars")
                                if len(items) >= max_items:
                                    break
                            except Exception as e:
                                logger.debug(f"⚠️ Erreur parsing item RSS: {e}")
                                continue
                        
                        if len(items) >= max_items:
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur RSS {f}: {e}")
                        continue
                        
            return items

        # Collecter des liens/articles via RSS en priorité
        # Yahoo Finance retiré pour éviter les plantages
        mw_rss = [
            'https://feeds.marketwatch.com/marketwatch/topstories/',
            'https://feeds.marketwatch.com/marketwatch/marketpulse/',
        ]
        # CNN RSS peut avoir des problèmes de connectivité, utiliser des alternatives
        cnn_rss = [
            'https://rss.cnn.com/rss/edition_world.rss',
            'https://rss.cnn.com/rss/edition_business.rss',
        ]
        # Flux RSS alternatifs qui fonctionnent
        alt_rss = [
            'https://feeds.bloomberg.com/markets/news.rss',
            'https://feeds.bloomberg.com/politics/news.rss',
            'https://www.ft.com/rss/home',
            'https://www.ft.com/rss/world',
            'https://www.ft.com/rss/companies',
            'https://www.cnbc.com/id/100003114/device/rss/rss.xml',
            'https://www.cnbc.com/id/10000664/device/rss/rss.xml',
        ]

        rss_items: List[ScrapedData] = []
        rss_items += await _fetch_rss_items(mw_rss, 'marketwatch', per_site * 3)
        rss_items += await _fetch_rss_items(cnn_rss, 'cnn', per_site * 3)
        # Fallback vers des flux alternatifs si les principaux échouent
        if len(rss_items) < per_site * 2:
            logger.info(f"📰 RSS principal: {len(rss_items)} articles, ajout de flux alternatifs...")
            rss_items += await _fetch_rss_items(alt_rss, 'alternative', per_site * 2)
        logger.info(f"📰 Total RSS collecté: {len(rss_items)} articles")

        # Fallback domain crawl SI explicitement autorisé
        mw_links = []
        cnn_links = []
        # Autoriser le crawl si RSS insuffisant OU si explicitement configuré
        allow_crawl = (len(rss_items) < per_site * 2) or (os.getenv('ALLOW_DOMAIN_CRAWL', 'false').lower() == 'true')
        # Robustesse: forcer le crawl si les RSS sont quasi nuls
        if len(rss_items) < per_site:
            allow_crawl = True
        logger.info(f"📰 RSS+state: collected={len(rss_items)} | allow_crawl={allow_crawl}")
        if allow_crawl:
            logger.info(f"📰 Domain crawl activé (RSS insuffisant: {len(rss_items)} < {per_site * 2})")
            if len([i for i in rss_items if i.metadata.get('source') == 'marketwatch']) < per_site:
                mw_links = await _gather_domain('www.marketwatch.com', marketwatch_starts, _is_mw_article, per_site * 2)
            if len([i for i in rss_items if i.metadata.get('source') == 'cnn']) < per_site:
                cnn_links = await _gather_domain('www.cnn.com', cnn_starts, _is_cnn_article, per_site * 2)
        else:
            logger.info("📰 Deep scrape: RSS-only mode (domain crawl disabled)")

        # Scraper les pages et filtrer
        items: List[ScrapedData] = list(rss_items)
        # Préparer les URLs issues des RSS pour enrichir le contenu (sans domain crawl)
        rss_mw_links = [i.url for i in rss_items if i.metadata.get('source') == 'marketwatch']
        rss_cnn_links = [i.url for i in rss_items if i.metadata.get('source') == 'cnn']
        
        # Ajouter des sites d'actualités financières directes si RSS insuffisant
        if len(rss_items) < per_site:
            logger.info("📰 Ajout de sites d'actualités financières directes...")
            direct_sites = [
                'https://www.reuters.com/markets/',
                'https://www.bloomberg.com/markets',
                'https://www.ft.com/markets',
                'https://www.cnbc.com/markets/',
            ]
            for site in direct_sites:
                try:
                    html = await self._scrape_with_params(site, {
                        'render_js': 'false',
                        'premium_proxy': 'true',
                        'block_resources': 'true',
                        'wait': '1200',
                        'country_code': 'us',
                    })
                    if html:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, 'lxml')
                        for a in soup.find_all('a', href=True):
                            href = a.get('href')
                            if href and any(domain in href for domain in ['/news/', '/story/', '/article/']):
                                if href.startswith('/'):
                                    href = f"https://{site.split('/')[2]}{href}"
                                if href not in [i.url for i in items]:
                                    items.append(ScrapedData(
                                        url=href,
                                        title=a.get_text()[:120] or href[:120],
                                        content='',
                                        timestamp=datetime.now(),
                                        metadata={'source': 'direct_scrape', 'scraped_at': datetime.now().isoformat()}
                                    ))
                                    if len(items) >= per_site * 2:
                                        break
                        if len(items) >= per_site * 2:
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Erreur scraping direct {site}: {e}")
                    continue

        async def _scrape_links(links: List[str], source_name: str):
            for url in links[:per_site]:
                try:
                    details = await self._scrape_page_with_metadata(url)
                    if not details or not details.get('text'):
                        continue
                    published_at = details.get('published_at')
                    # Normalize to aware UTC
                    if published_at and published_at.tzinfo is None:
                        try:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                        except Exception:
                            pass
                    if not _is_recent_dt(published_at):
                        continue
                    text = details.get('text') or ''
                    # Filtrer grossièrement sur la requête si précisée
                    if topic_query and isinstance(topic_query, str):
                        q = topic_query.lower().strip()
                        if q and (q not in (text.lower() or '')):
                            # garder quand même si c'est du market summary générique
                            pass
                    items.append(ScrapedData(
                        url=url,
                        title=url[:120],
                        content=text[:8000],
                        timestamp=published_at or _now_utc(),
                        metadata={'source': source_name, 'scraped_at': datetime.now().isoformat()}
                    ))
                except Exception:
                    continue

        # Enrichir d'abord à partir des liens RSS (texte complet)
        await _scrape_links(rss_mw_links, 'marketwatch')
        await _scrape_links(rss_cnn_links, 'cnn')

        if mw_links:
            await _scrape_links(mw_links, 'marketwatch')
        if cnn_links:
            await _scrape_links(cnn_links, 'cnn')

        # Assurer un minimum de caractères
        def _total_chars(data: List[ScrapedData]) -> int:
            return sum(len((d.content or '')) for d in data)

        total_chars = _total_chars(items)
        if total_chars < min_chars:
            # Essayer d'élargir le nombre de liens (jusqu'à 2x per_site)
            extra_items: List[ScrapedData] = []
            async def _scrape_more(links: List[str], source_name: str):
                for url in links[per_site:per_site*2]:
                    try:
                        details = await self._scrape_page_with_metadata(url)
                        if not details or not details.get('text'):
                            continue
                        published_at = details.get('published_at')
                        if not _is_recent_dt(published_at):
                            continue
                        text = details.get('text') or ''
                        extra_items.append(ScrapedData(
                            url=url,
                            title=url[:120],
                            content=text[:8000],
                            timestamp=published_at or datetime.now(),
                            metadata={'source': source_name, 'scraped_at': datetime.now().isoformat()}
                        ))
                        if _total_chars(items + extra_items) >= min_chars:
                            break
                    except Exception:
                        continue

            # Essayer d'abord plus d'articles depuis les liens RSS
            await _scrape_more(rss_mw_links, 'marketwatch')
            if _total_chars(items + extra_items) < min_chars:
                await _scrape_more(rss_cnn_links, 'cnn')
            # Si autorisé, compléter via un crawl léger
            if allow_crawl and _total_chars(items + extra_items) < min_chars:
                await _scrape_more(mw_links, 'marketwatch')
            if allow_crawl and _total_chars(items + extra_items) < min_chars:
                await _scrape_more(cnn_links, 'cnn')
            items.extend(extra_items)

        # Trier par fraîcheur, limiter au besoin
        items = [it for it in items if it and it.content]
        # Ensure timestamps are comparable (aware UTC)
        def _key_ts(x: ScrapedData) -> datetime:
            ts = x.timestamp or _now_utc()
            try:
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                pass
            return ts
        items.sort(key=_key_ts, reverse=True)
        logger.info(f"📰 Deep scrape: {len(items)} articles récents | chars={sum(len(i.content) for i in items)}")
        return items

    async def search_and_scrape_swiss(self, topic_query: str, per_site: int = 10, max_age_hours: int = 72, min_chars: int = 15000) -> List[ScrapedData]:
        """Scrape ciblé Suisse via Le Temps (RSS), SNB (RSS) et deep-crawl RTS.

        - Sources principales:
          • RSS: https://www.letemps.ch/articles.rss, https://www.snb.ch/public/fr/rss/news
          • Deep-crawl: https://www.rts.ch/info/ (ouvre les liens info)
        - Filtre: articles publiés dans les dernières max_age_hours
        - Objectif: total contenu >= min_chars
        """
        if not self._initialized:
            await self.initialize()

        def _now_utc() -> datetime:
            try:
                return datetime.now(timezone.utc)
            except Exception:
                return datetime.utcnow().replace(tzinfo=timezone.utc)

        def _normalize_ts(dt_obj: Optional[datetime]) -> Optional[datetime]:
            if not dt_obj:
                return None
            try:
                if dt_obj.tzinfo is None:
                    return dt_obj.replace(tzinfo=timezone.utc)
                return dt_obj.astimezone(timezone.utc)
            except Exception:
                return dt_obj

        def _is_recent_dt(dt: Optional[datetime]) -> bool:
            try:
                if not dt:
                    return False
                dtz = _normalize_ts(dt)
                nowz = _now_utc()
                if dtz and dtz.tzinfo is None:
                    dtz = dtz.replace(tzinfo=timezone.utc)
                if nowz.tzinfo is None:
                    nowz = nowz.replace(tzinfo=timezone.utc)
                return (nowz - dtz) <= timedelta(hours=max_age_hours)
            except Exception:
                return False

        async def _gather_domain(domain: str, start_urls: List[str], link_predicate, max_links: int) -> List[str]:
            links: List[str] = []
            seen: set = set()
            for start in start_urls:
                try:
                    html = await self._scrape_with_params(start, {
                        'render_js': 'false',
                        'premium_proxy': 'true',
                        'block_resources': 'true',
                        'wait': '1200',
                        'country_code': 'ch',
                    })
                    if not html:
                        continue
                    from bs4 import BeautifulSoup  # type: ignore
                    soup = BeautifulSoup(html or '', 'lxml')
                    for a in soup.find_all('a'):
                        href = a.get('href') or ''
                        if not href:
                            continue
                        if href.startswith('/'):
                            href = f"https://{domain}{href}"
                        if (domain in href) and link_predicate(href) and href not in seen:
                            seen.add(href)
                            links.append(href)
                        if len(links) >= max_links:
                            break
                except Exception:
                    continue
                if len(links) >= max_links:
                    break
            return links

        # Helpers RSS (Le Temps, SNB)
        async def _fetch_rss_items(feeds: List[str], source_name: str, max_items: int) -> List[ScrapedData]:
            items: List[ScrapedData] = []
            try:
                import xml.etree.ElementTree as ET  # lightweight
            except Exception:
                return items

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                for f in feeds:
                    try:
                        text = None
                        try:
                            async with session.get(f, timeout=12) as resp:
                                if resp.status == 200:
                                    text = await resp.text()
                        except Exception:
                            text = None
                        if not text and self.api_key and self.api_key != 'test_key_for_testing':
                            try:
                                async with session.get(self.base_url, params={
                                    'api_key': self.api_key,
                                    'url': f,
                                    'render_js': 'false',
                                    'premium_proxy': 'true',
                                    'country_code': 'ch'
                                }, timeout=15) as r2:
                                    if r2.status == 200:
                                        text = await r2.text()
                            except Exception:
                                pass
                        if not text:
                            continue
                        try:
                            root = ET.fromstring(text)
                        except Exception:
                            continue
                        for item in root.findall('.//item'):
                            try:
                                link_el = item.find('link')
                                title_el = item.find('title')
                                desc_el = item.find('description')
                                pub_el = item.find('pubDate')
                                link = (link_el.text or '').strip() if link_el is not None else ''
                                title = (title_el.text or '').strip() if title_el is not None else link[:120]
                                desc = (desc_el.text or '').strip() if desc_el is not None else ''
                                ts = self._parse_datetime_str(pub_el.text) if pub_el is not None else None
                                ts = _normalize_ts(ts)
                                if ts and (_now_utc() - ts) > timedelta(hours=max_age_hours):
                                    continue
                                items.append(ScrapedData(
                                    url=link,
                                    title=title[:120],
                                    content=desc[:4000] if desc else title[:200],
                                    timestamp=ts or _now_utc(),
                                    metadata={'source': source_name, 'from': 'rss'}
                                ))
                                if len(items) >= max_items:
                                    break
                            except Exception:
                                continue
                        if len(items) >= max_items:
                            break
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur RSS {f}: {e}")
                        continue
            return items

        # Deep-crawl RTS (info)
        def _is_rts_article(url: str) -> bool:
            u = url.lower()
            return ('rts.ch' in u) and ('/info/' in u) and any(p in u for p in ['/article', '/monde', '/suisse', '/economie', '/politique'])

        rts_starts = [
            'https://www.rts.ch/info/',
            'https://www.rts.ch/info/suisse/',
            'https://www.rts.ch/info/economie/',
            'https://www.rts.ch/info/monde/'
        ]

        # Deep-crawl Immobilien Business (immobilier CH)
        def _is_immobilien_article(url: str) -> bool:
            u = url.lower()
            return ('immobilienbusiness.ch' in u) and ('/de/' in u) and not any(x in u for x in ['/shop', '/kontakt', '/agb', '/datenschutz'])

        immobilien_starts = [
            'https://www.immobilienbusiness.ch/de/',
            'https://www.immobilienbusiness.ch/de/residential/',
            'https://www.immobilienbusiness.ch/de/regionen/',
            'https://www.immobilienbusiness.ch/de/unternehmen/'
        ]

        items: List[ScrapedData] = []

        # 1) RSS Le Temps + SNB
        try:
            rss_list: List[ScrapedData] = []
            rss_list += await _fetch_rss_items(['https://www.letemps.ch/articles.rss'], 'letemps', per_site * 3)
            rss_list += await _fetch_rss_items(['https://www.snb.ch/public/fr/rss/news'], 'snb', per_site * 2)
            items.extend(rss_list)
        except Exception:
            pass

        # 2) Deep crawl RTS links and scrape
        try:
            rts_links = await _gather_domain('www.rts.ch', rts_starts, _is_rts_article, per_site * 4)
        except Exception:
            rts_links = []

        # 3) Deep crawl Immobilien Business links and scrape
        try:
            immo_links = await _gather_domain('www.immobilienbusiness.ch', immobilien_starts, _is_immobilien_article, per_site * 3)
        except Exception:
            immo_links = []

        async def _scrape_links(links: List[str], source_name: str):
            for url in links[:per_site*2]:
                try:
                    details = await self._scrape_page_with_metadata(url)
                    if not details or not details.get('text'):
                        continue
                    published_at = details.get('published_at')
                    # Normalize to aware UTC
                    if published_at and getattr(published_at, 'tzinfo', None) is None:
                        try:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                        except Exception:
                            pass
                    if not _is_recent_dt(published_at):
                        continue
                    text = details.get('text') or ''
                    items.append(ScrapedData(
                        url=url,
                        title=url[:120],
                        content=text[:8000],
                        timestamp=published_at or _now_utc(),
                        metadata={'source': source_name, 'scraped_at': datetime.now().isoformat()}
                    ))
                except Exception:
                    continue

        if 'rts_links' in locals() and rts_links:
            await _scrape_links(rts_links, 'rts')
        if 'immo_links' in locals() and immo_links:
            await _scrape_links(immo_links, 'immobilienbusiness')

        # Assurer un minimum de caractères
        def _total_chars(data: List[ScrapedData]) -> int:
            return sum(len((d.content or '')) for d in data)

        total_chars = _total_chars(items)
        if total_chars < min_chars:
            # Étendre si nécessaire
            if 'rts_links' in locals() and rts_links:
                await _scrape_links(rts_links[per_site*2:per_site*3], 'rts')
            if 'immo_links' in locals() and immo_links:
                await _scrape_links(immo_links[per_site:per_site*2], 'immobilienbusiness')

        # Trier et retourner (assurer timestamps comparables UTC-aware)
        items = [it for it in items if it and it.content]
        def _key_ts(x: ScrapedData) -> datetime:
            ts = x.timestamp or _now_utc()
            try:
                if getattr(ts, 'tzinfo', None) is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                pass
            return ts
        items.sort(key=_key_ts, reverse=True)
        logger.info(f"🇨🇭 Swiss scrape: {len(items)} articles récents | chars={sum(len(i.content) for i in items)}")
        return items

    async def execute_swiss_market_update(self, prompt: str) -> Dict:
        """Exécute le pipeline Suisse: scrape CH → snapshot → LLM JSON."""
        try:
            min_chars = int(os.getenv('LLM_MIN_CONTEXT_CHARS', '15000'))
            scraped = await self.search_and_scrape_swiss(topic_query='marché suisse', per_site=10, max_age_hours=72, min_chars=min_chars)
            if not scraped:
                return { 'error': 'Aucune donnée suisse récente trouvée' }
            # Rapport Suisse: pas de récupération de cours/bourse → pas de snapshot
            result = await self.process_with_llm(prompt, scraped, {})
            return result
        except Exception as e:
            logger.error(f"❌ Erreur execute_swiss_market_update: {e}")
            return { 'error': str(e) }

    async def execute_global_market_update(self, prompt: str) -> Dict:
        """Pipeline GLOBAL MARKET UPDATE: <24h news (incl. Google News) → snapshot → LLM JSON."""
        try:
            # Paramètres par défaut
            per_site = int(os.getenv('GLOBAL_PER_SITE', '20'))
            max_age_hours = int(os.getenv('GLOBAL_MAX_AGE_HOURS', '24'))
            min_chars = int(os.getenv('LLM_MIN_CONTEXT_CHARS', '30000'))

            # Étape 1: Scrape profond multi-sources (<24h)
            scraped = await self.search_and_scrape_deep(
                topic_query='marché global',
                per_site=per_site,
                max_age_hours=max_age_hours,
                min_chars=min_chars
            )

            # Étape 1b: Google News (FR) – enrichissement liens récents
            async def _fetch_google_news_links(queries: list, hl: str = 'fr', gl: str = 'CH', ceid: str = 'CH:fr', max_items: int = 20) -> list:
                import xml.etree.ElementTree as ET
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36'
                }
                items = []
                async with aiohttp.ClientSession(headers=headers) as session:
                    for q in queries:
                        try:
                            feed_url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"
                            # Essai direct
                            text = None
                            try:
                                async with session.get(feed_url, timeout=10) as resp:
                                    if resp.status == 200:
                                        text = await resp.text()
                            except Exception:
                                pass
                            # Fallback via ScrapingBee (sans JS)
                            if not text and self.api_key and self.api_key != 'test_key_for_testing':
                                try:
                                    async with session.get(self.base_url, params={
                                        'api_key': self.api_key,
                                        'url': feed_url,
                                        'render_js': 'false'
                                    }, timeout=15) as r2:
                                        if r2.status == 200:
                                            text = await r2.text()
                                except Exception:
                                    pass
                            if not text:
                                continue
                            try:
                                root = ET.fromstring(text)
                            except Exception:
                                continue
                            for item in root.findall('.//item'):
                                try:
                                    link_el = item.find('link')
                                    title_el = item.find('title')
                                    pub_el = item.find('pubDate')
                                    link = (link_el.text or '').strip() if link_el is not None else ''
                                    title = (title_el.text or '').strip() if title_el is not None else link[:120]
                                    if not link:
                                        continue
                                    items.append({'url': link, 'title': title})
                                    if len(items) >= max_items:
                                        break
                                except Exception:
                                    continue
                            if len(items) >= max_items:
                                break
                        except Exception:
                            continue
                return items

            try:
                queries = [
                    'banques centrales', 'inflation', 'PMI', 'PIB', 'chômage',
                    'EUR/CHF', 'USD/CHF', 'énergie', 'Fed', 'BCE', 'BNS', 'PBoC', 'BoJ'
                ]
                gn_links = await _fetch_google_news_links(queries, hl='fr', gl='CH', ceid='CH:fr', max_items=per_site)
                # Scraper le contenu des liens Google News (limité)
                added = 0
                for it in gn_links:
                    if added >= per_site:
                        break
                    try:
                        # Résoudre la redirection vers l’éditeur final
                        target_url = it['url']
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(target_url, allow_redirects=True, timeout=15) as resp:
                                    target_url = str(resp.url)
                        except Exception:
                            pass
                        details = await self._scrape_page_with_metadata(target_url)
                        if not details or not details.get('text'):
                            continue
                        published_at = details.get('published_at') or datetime.now()
                        scraped.append(ScrapedData(
                            url=target_url,
                            title=(it.get('title') or target_url)[:120],
                            content=(details.get('text') or '')[:8000],
                            timestamp=published_at,
                            metadata={'source': 'google_news', 'scraped_at': datetime.now().isoformat()}
                        ))
                        added += 1
                    except Exception:
                        continue
            except Exception:
                pass

            # Étape 1c: RSS supplémentaires confirmés (activés par défaut)
            try:
                async def _fetch_generic_rss(feeds: List[str], source_name: str, max_items: int) -> List[ScrapedData]:
                    items: List[ScrapedData] = []
                    try:
                        import xml.etree.ElementTree as ET
                    except Exception:
                        return items
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36'
                    }
                    async with aiohttp.ClientSession(headers=headers) as session:
                        for f in feeds:
                            text = None
                            try:
                                async with session.get(f, timeout=15) as resp:
                                    if resp.status == 200:
                                        text = await resp.text()
                                    else:
                                        logger.warning(f"⚠️ RSS fetch failed ({resp.status}): {f}")
                            except Exception as e:
                                logger.warning(f"⚠️ RSS fetch error: {f} ({e})")

                            # ScrapingBee fallback
                            if not text and self.api_key and self.api_key != 'test_key_for_testing':
                                try:
                                    async with session.get(self.base_url, params={
                                        'api_key': self.api_key,
                                        'url': f,
                                        'render_js': 'false'
                                    }, timeout=20) as r2:
                                        if r2.status == 200:
                                            text = await r2.text()
                                        else:
                                            logger.warning(f"⚠️ RSS SBee failed ({r2.status}): {f}")
                                except Exception as e:
                                    logger.warning(f"⚠️ RSS SBee error: {f} ({e})")

                            if not text:
                                logger.warning(f"⚠️ RSS ignored (no content): {f}")
                                continue

                            try:
                                root = ET.fromstring(text)
                            except Exception as e:
                                logger.warning(f"⚠️ RSS parse error: {f} ({e})")
                                continue

                            for item in root.findall('.//item'):
                                try:
                                    link_el = item.find('link')
                                    title_el = item.find('title')
                                    desc_el = item.find('description')
                                    pub_el = item.find('pubDate')
                                    link = (link_el.text or '').strip() if link_el is not None else ''
                                    title = (title_el.text or '').strip() if title_el is not None else link[:120]
                                    desc = (desc_el.text or '').strip() if desc_el is not None else ''
                                    ts = self._parse_datetime_str(pub_el.text) if pub_el is not None else None
                                    if not link:
                                        continue
                                    items.append(ScrapedData(
                                        url=link,
                                        title=title[:120],
                                        content=desc[:4000] if desc else title[:200],
                                        timestamp=ts or datetime.now(),
                                        metadata={'source': source_name, 'from': 'rss'}
                                    ))
                                    if len(items) >= max_items:
                                        break
                                except Exception:
                                    continue

                            if len(items) >= max_items:
                                break

                    return items

                extra_feeds = [
                    # Suisse
                    'https://www.snb.ch/public/fr/rss/news',
                    # Europe (si ce flux n'est pas XML, il sera ignoré)
                    'https://www.ecb.europa.eu/rss/',
                    # US
                    'https://www.federalreserve.gov/feeds/',
                    # Énergie
                    'https://www.eia.gov/rss/todayinenergy.xml',
                    # Presse
                    'https://www.letemps.ch/articles.rss',
                    # Marchés
                    'https://feeds.reuters.com/reuters/marketsNews'
                ]
                extra_items = await _fetch_generic_rss(extra_feeds, 'extra_rss', max_items=per_site)
                # Déduplication par URL
                seen = set(x.url for x in scraped)
                for it in extra_items:
                    if it.url not in seen:
                        scraped.append(it)
                        seen.add(it.url)
                # Enrichissement: suivre les liens RSS extra et scraper le texte complet
                try:
                    enrich_extra = str(os.getenv('EXTRA_RSS_ENRICH', '1')).lower() in ('1', 'true', 'yes', 'on')
                except Exception:
                    enrich_extra = True
                if enrich_extra:
                    max_enrich = max(1, min(per_site, len(scraped)))
                    enriched = 0
                    logger.info(f"📰 Enrichissement des flux RSS extra (max {max_enrich})…")
                    for idx, it in enumerate(list(scraped)):
                        if enriched >= max_enrich:
                            break
                        try:
                            if isinstance(it.metadata, dict) and it.metadata.get('source') == 'extra_rss':
                                details = await self._scrape_page_with_metadata(it.url)
                                if details and details.get('text'):
                                    published_at = details.get('published_at') or it.timestamp
                                    scraped[idx] = ScrapedData(
                                        url=it.url,
                                        title=it.title,
                                        content=(details.get('text') or '')[:8000],
                                        timestamp=published_at,
                                        metadata={**it.metadata, 'enriched': '1'}
                                    )
                                    enriched += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Enrichissement RSS extra échoué: {it.url} ({e})")
                    logger.info(f"📰 Enrichissement terminé: {enriched} article(s) enrichi(s)")
            except Exception:
                pass

            if not scraped:
                return {'error': "Aucune donnée récente trouvée (<24h)"}

            # Étape 2: Snapshot de marché quasi temps réel
            from stock_api_manager import stock_api_manager
            market_snapshot = stock_api_manager.get_market_snapshot()

            # Étape 3: Appel LLM avec tokens étendus (45k) et reasoning 'high'
            result = await self.process_with_llm_custom(
                prompt=prompt,
                scraped_data=scraped,
                market_snapshot=market_snapshot,
                max_tokens=int(os.getenv('GLOBAL_MAX_OUTPUT_TOKENS', '45000')),
                reasoning_effort=os.getenv('GLOBAL_REASONING_EFFORT', 'high')
            )
            return result
        except Exception as e:
            logger.error(f"❌ Erreur execute_global_market_update: {e}")
            return { 'error': str(e) }

    async def process_with_llm_custom(self, prompt: str, scraped_data: List[ScrapedData], market_snapshot: Dict, max_tokens: int = 45000, reasoning_effort: str = 'high') -> Dict:
        """Wrapper pour forcer max tokens et reasoning sans impacter les autres flux."""
        prev_tokens = os.getenv('LLM_MAX_OUTPUT_TOKENS')
        prev_reason = os.getenv('AI_REASONING_EFFORT')
        try:
            os.environ['LLM_MAX_OUTPUT_TOKENS'] = str(max_tokens)
            os.environ['AI_REASONING_EFFORT'] = str(reasoning_effort)
            return await self.process_with_llm(prompt, scraped_data, market_snapshot)
        finally:
            if prev_tokens is not None:
                os.environ['LLM_MAX_OUTPUT_TOKENS'] = prev_tokens
            else:
                os.environ.pop('LLM_MAX_OUTPUT_TOKENS', None)
            if prev_reason is not None:
                os.environ['AI_REASONING_EFFORT'] = prev_reason
            else:
                os.environ.pop('AI_REASONING_EFFORT', None)
    # search_x_recent retiré (X.com désactivé)
    
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
                    # Géopolitique majeure (ajout CNN)
                    {
                        'url': "https://www.cnn.com/world",
                        'title': "CNN - World / Geopolitics"
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
        """Scrape une page et renvoie le texte + date de publication si détectable.

        Optimisations:
        - Pour HTML nécessitant consent/hydratation, active JS + premium proxy US + blocage des ressources + petit scénario si besoin
        """
        try:
            # Heuristique: certaines pages exigent JS (consent/hydratation)
            u = (url or '').lower()
            needs_js = any(k in u for k in ['marketwatch.com', 'cnn.com', '/quote/', '/key-statistics'])
            # Pays par défaut: 'ch' pour domaines suisses connus sinon 'us'
            is_swiss_domain = any(d in u for d in ['.ch', 'rts.ch', 'letemps.ch', 'snb.ch', 'nzz.ch', 'agefi.com', 'immobilienbusiness.ch'])
            country = 'ch' if is_swiss_domain else 'us'
            timeout_secs = int(os.getenv('SCRAPINGBEE_HTTP_TIMEOUT', '30'))
            params = {
                'api_key': self.api_key,
                'url': url,
                'render_js': 'true' if needs_js else 'false',
                'premium_proxy': 'true',
                'block_resources': 'true' if needs_js else 'false',
                'country_code': country,
                'wait': '2000' if needs_js else '1200'
            }
            # Google domains require custom_google=true (charged) per ScrapingBee
            try:
                if 'news.google.com' in u or (u.startswith('https://www.google.') or '://www.google.' in u):
                    params['custom_google'] = 'true'
            except Exception:
                pass
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_secs)) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        # Log détaillé pour diagnostiquer les 4xx/5xx
                        try:
                            response_text = await response.text()
                        except Exception:
                            response_text = ''
                        logger.error(f"❌ Erreur ScrapingBee scraping: {response.status}")
                        logger.error(f"URL: {url}")
                        logger.error(f"Params: {params}")
                        if response_text:
                            logger.error(f"Réponse de ScrapingBee: {response_text}")
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
        """Parse datetime string with better RSS support"""
        try:
            if not s or not isinstance(s, str):
                return None
                
            st = s.strip()
            if not st:
                return None
                
            # RSS format: "Thu, 28 Aug 2025 15:52:00 GMT"
            if ',' in st and len(st.split()) >= 6:
                try:
                    from email.utils import parsedate_to_datetime
                    return parsedate_to_datetime(st)
                except Exception:
                    pass
            
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
                pass
                
            # Fallback: try common RSS patterns
            import re
            patterns = [
                r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, st, re.IGNORECASE)
                if match:
                    try:
                        if len(match.groups()) == 3:
                            if pattern == patterns[0]:  # "28 Aug 2025"
                                month_map = {
                                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                                }
                                day, month_str, year = match.groups()
                                month = month_map.get(month_str.lower(), 1)
                                return datetime(int(year), month, int(day))
                            elif pattern == patterns[1]:  # "2025-08-28"
                                year, month, day = match.groups()
                                return datetime(int(year), int(month), int(day))
                            elif pattern == patterns[2]:  # "08/28/2025"
                                month, day, year = match.groups()
                                return datetime(int(year), int(month), int(day))
                    except Exception:
                        continue
                        
        except Exception:
            pass
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

            timeout_secs = int(os.getenv('SCRAPINGBEE_HTTP_TIMEOUT', '30'))
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_secs)) as session:
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
            strict_mode = str(os.getenv('STRICT_LLM_JSON', '0')).strip() in ('1', 'true', 'True')
            
            # Prompt système chargé depuis un fichier (aucun fallback embarqué)
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'market_analysis_fr.txt')
            with open(prompt_path, 'r', encoding='utf-8') as _pf:
                system_prompt = _pf.read()
            
            # Préparer le contexte (avec limitation stricte)
            context_complete = self._prepare_context(scraped_data)
            max_context_chars = int(os.getenv('LLM_CONTEXT_MAX_CHARS', '150000'))
            if len(context_complete) > max_context_chars:
                context = context_complete[:max_context_chars]
                truncated = True
            else:
                context = context_complete
                truncated = False
            try:
                snapshot_str = json.dumps(market_snapshot or {}, ensure_ascii=False)
            except Exception:
                snapshot_str = '{}'
            max_snapshot_chars = int(os.getenv('LLM_SNAPSHOT_MAX_CHARS', '60000'))
            if len(snapshot_str) > max_snapshot_chars:
                snapshot_str = snapshot_str[:max_snapshot_chars]
                snapshot_truncated = True
            else:
                snapshot_truncated = False
            logger.info(
                f"🧠 Contexte OpenAI: context_len={len(context)} (truncated={truncated}) | snapshot_len={len(snapshot_str)} (truncated={snapshot_truncated}) | sources={len(scraped_data)}"
            )

            # Paramètres adaptatifs (rate limit/429)
            current_max_tokens = int(os.getenv('LLM_MAX_OUTPUT_TOKENS', '30000'))
            context_shrink = 1.0
            snapshot_shrink = 1.0
            base_context = context
            base_snapshot = snapshot_str

            # Prompt système optimisé (GPT‑5) — verbosité/raisonnement renforcés, géopolitique à jour, indicateurs extraits du scrap
            # system_prompt = """
            # Tu es un Directeur de Recherche Senior (finance quantitative, géopolitique appliquée, IA). Audience: C‑Suite, gérants institutionnels, trading floor. Mission: produire une analyse EXHAUSTIVE, TRÈS DÉTAILLÉE et rigoureusement argumentée. Ne sois pas permissif ni paresseux.

            # LANGUE: Français (fr-FR). Rédige TOUT le contenu en français (executive_summary, summary, key_points, insights, risks, opportunities, structured_data, geopolitical, economic_indicators). Si les sources sont en anglais, TRADUIS fidèlement en français sans insérer de phrases en anglais. N'insère AUCUNE URL/citation ni section "Sources" dans le narratif.

            # Cadre analytique:
            # - Hiérarchie cognitive (Micro/Méso/Macro/Méta), intégration temporelle (T‑1/T0/T+1), analyse causale (catalyst → effets 2e ordre → chaînes).
            # - Explicite les mécanismes de transmission, indicateurs menant/retardés, et conditions de rupture de régime.

            # Règles de données:
            # - Priorité absolue aux valeurs du market_snapshot (vérité temps quasi réel).
            # - Exploite STRICTEMENT les articles scrappés (contexte fourni) et privilégie les nouvelles récentes (≤ 48–72h; <24h si dispo). Ignore les extrapolations non sourcées.
            # - Jamais inventer. Si absent → "N/D" avec explication. Chiffres systématiquement sourcés (titre+URL) quand issus du scrap.
            # - Signale divergences prix/volume (>20% 20j), sectorielles (z>2), géographiques (>1σ).

            # FORMAT DE SORTIE CRITIQUE:
            # - Retourne UNIQUEMENT un objet JSON valide, sans texte avant/après.
            # - Le champ 'summary' doit être une STRING, pas un JSON stringifié.
            # - Tous les champs de type array doivent être des listes Python valides.
            # - Aucun champ ne doit contenir de JSON imbriqué stringifié.
            # - TOUTES les chaînes de caractères doivent être correctement échappées.
            # - TOUTES les accolades et crochets doivent être équilibrés.
            # - Vérifie que le JSON est syntaxiquement correct avant de le retourner.
            # - IMPORTANT: La réponse DOIT être un seul objet JSON COMPLET ET FERMÉ (aucune troncature). Si tu détectes un risque de coupure, corrige et renvoie un objet complet.

            # Sortie STRICTEMENT en JSON unique. Compatibilité requise avec notre backend:
            # - Fournis AUSSI les champs legacy: 
            #   - executive_summary: 10 bullets (obligatoire, denses et actionnables),
            #   - summary: narrative approfondie (≥4000 caractères) avec raisonnement structuré,
            #   - key_points: ≥12 points à haut signal,
            #   - structured_data: inclut les sections avancées ci‑dessous,
            #   - insights: ≥3 insights actionnables (OBLIGATOIRE, jamais vide),
            #   - risks: ≥3 risques identifiés (OBLIGATOIRE, jamais vide),
            #   - opportunities: ≥3 opportunités (OBLIGATOIRE, jamais vide),
            #   - sources: liste des sources utilisées,
            #   - confidence_score: score de confiance (0.0–1.0).

            # IMPORTANT: Les champs insights, risks, et opportunities ne doivent JAMAIS être des listes vides.
            # Si tu n'as pas d'informations spécifiques, génère du contenu pertinent basé sur l'analyse.

            # Schéma attendu (extrait):
            # {
            #   "meta_analysis": { "regime_detection": { "market_regime": "risk-on|risk-off|transition", "volatility_regime": "low|normal|stressed|crisis", "liquidity_state": "abundant|normal|tight|frozen", "confidence": 0.00 }, "key_drivers": { "primary": "...", "secondary": ["..."], "emerging": ["..."] }},
            #   "executive_dashboard": { "alert_level": "🟢|🟡|🔴", "top_trades": [{ "action": "LONG|SHORT|HEDGE", "instrument": "TICKER", "rationale": "<50 mots", "risk_reward": "X:Y", "timeframe": "intraday|1W|1M", "confidence": 0.00 }], "snapshot_metrics": ["• lignes avec valeurs issues du market_snapshot"] },
            #   "deep_analysis": { "narrative": "4000+ caractères", "sector_rotation_matrix": { "outperformers": [{"sector":"...","performance":"%","catalyst":"...","momentum":"accelerating|stable|decelerating"}], "underperformers": [{"sector":"...","performance":"%","reason":"...","reversal_probability":"low|medium|high"}] }, "correlation_insights": { "breaking_correlations": ["..."], "new_relationships": ["..."], "regime_dependent": ["..."] }, "ai_focus_section": { "mega_caps": {"NVDA": {"price": 0, "change": 0, "rsi": 0, "volume_ratio": 0}, "MSFT": {"price": 0, "change": 0}}, "supply_chain": "...", "investment_flows": "..." }, "geopolitical_chess": { "immediate_impacts": [{"event":"(événement géopolitique précis, daté ≤72h)","affected_assets":["..."],"magnitude":"bp/%","duration":"court|moyen|long","sources":[{"title":"...","url":"..."}]}], "second_order_effects": [{"trigger":"...","cascade":"...","probability":0.00,"hedge":"..."}], "black_swans": [{"scenario":"...","probability":0.00,"impact":"catastrophic|severe|moderate","early_warning":"..."}] } },
            #   "quantitative_signals": { "technical_matrix": { "oversold": ["..."], "overbought": ["..."], "breakouts": ["..."], "divergences": ["..."] }, "options_flow": { "unusual_activity": ["..."], "large_trades": ["..."], "implied_moves": ["..."] }, "smart_money_tracking": { "institutional_flows": "...", "insider_activity": "...", "sentiment_divergence": "..." } },
            #   "risk_management": { "portfolio_adjustments": [{"current_exposure":"...","recommended_change":"...","rationale":"...","implementation":"..."}], "tail_risk_hedges": [{"risk":"...","probability":0.00,"hedge_strategy":"...","cost":"bp/%","effectiveness":"1-10"}], "stress_test_results": { "scenario_1": {"name":"..."}, "scenario_2": {"name":"..."} } },
            #   "actionable_summary": { "immediate_actions": ["..."], "watchlist": ["..."], "key_metrics_alerts": { "if_breaks": ["..."], "if_holds": ["..."], "calendar": ["..."] } },
            #   "economic_indicators": { "inflation": {"US": "<valeur%>", "EU": "<valeur%>"}, "central_banks": ["Fed <taux%>", "BCE <taux%>"], "gdp_growth": {"US": "<valeur%>", "China": "<valeur%>"}, "unemployment": {"US": "<valeur%>", "EU": "<valeur%>"}, "additional_indicators": [{"name":"PMI Manufacturing US","value":"<valeur>","period":"<mois>","source":"<titre>"}] },
            #   "metadata": { "report_timestamp": "YYYY-MM-DD HH:MM:SS UTC", "data_quality_score": 0.00, "model_confidence": 0.00 }
            # }

            # Exigences géopolitiques (obligatoire):
            # - Analyse géopolitique à jour issue des DERNIÈRES nouvelles scrappées (≤72h), en priorité depuis Reuters, FT, Bloomberg, CNN (rubrique World) et X.com (≤12h). Si plusieurs versions d’un même événement, privilégie la plus récente et cite la source (titre+URL).
            # - Détaille causes → effets de 2e ordre → risques de queue; propose hedges concrets.

            # Exigences indicateurs (obligatoire):
            # - Extrait les indicateurs explicitement mentionnés dans les articles (CPI/PPI, Core CPI/PCE, PMI/ISM, NFP/chômage, retail sales, GDP/GDPNow, Fed/BCE/BoE/BoJ, VIX…).
            # - Renseigne le bloc economic_indicators ci‑dessus avec des valeurs lisibles (unités et période implicites via le texte) quand disponibles; sinon "N/D".

            # Contraintes générales:
            # - Utiliser exclusivement les chiffres du market_snapshot pour les prix/variations; compléter avec le scrap pour le narratif et les indicateurs macro.
            # - Style trading floor: direct, technique; gras Markdown pour points critiques; pas de HTML.
            # - Emojis sobres et professionnels pour signaler tendances/risques/insights: 📈/📉 (tendances), 🟢/🟡/🔴 (régime/alerte), ⚠️ (risque), 💡 (insight), 🏦 (banques centrales), 🌍 (macro/géo), ⏱️ (temporalité), 📊 (métriques). Fréquence: 1–2 par section max; jamais dans les nombres ou clés JSON.
            # - Répondre en UN SEUL objet JSON valide.
            # """
            
            chosen_model = os.getenv("AI_MODEL", "gpt-5")
            logger.info(f"🤖 Appel à l'API OpenAI ({chosen_model}) en cours pour une analyse exhaustive (prompt renforcé)...")
            
            # Essayer jusqu'à 3 fois en cas d'erreur
            for attempt in range(3):
                try:
                    # Ajuster contexte/snapshot par tentative (en cas de 429)
                    attempt_context_len = max(1000, int(len(base_context) * context_shrink))
                    attempt_snapshot_len = max(500, int(len(base_snapshot) * snapshot_shrink))
                    attempt_context = base_context[:attempt_context_len]
                    attempt_snapshot = base_snapshot[:attempt_snapshot_len]
                    logger.info(f"🔁 Tentative {attempt+1}/3: max_tokens={current_max_tokens}, ctx={len(attempt_context)}, snap={len(attempt_snapshot)}")
                    # Responses API (reasoning ready)
                    input_messages = [
                        {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                        {"role": "user", "content": [{
                            "type": "input_text",
                            "text": f"Demande: {prompt}\n\nDONNÉES FACTUELLES (snapshot):\n{attempt_snapshot}\n\nDONNÉES COLLECTÉES (articles):\n{attempt_context}"
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
                    effort = os.getenv("AI_REASONING_EFFORT", "high")
                    if effort:
                        req_kwargs["reasoning"] = {"effort": effort}

                    # Utiliser exclusivement Responses API (JSON garanti)
                    from gpt5_compat import from_responses_simple, extract_output_text
                    # Schéma JSON strict pour garantir les sections (et contraindre min items)
                    json_schema = {
                        "name": "MarketAnalysis",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "executive_summary": {"type": "array", "items": {"type": "string"}},
                                "summary": {"type": "string"},
                                "key_points": {"type": "array", "items": {"type": "string"}},
                                "structured_data": {"type": "object"},
                                "geopolitical_analysis": {"type": "object"},
                                "economic_indicators": {"type": "object"},
                                "insights": {"type": "array", "minItems": 3, "items": {"type": "string"}},
                                "risks": {"type": "array", "minItems": 3, "items": {"type": "string"}},
                                "opportunities": {"type": "array", "minItems": 3, "items": {"type": "string"}},
                                "sources": {"type": "array"},
                                "confidence_score": {"type": "number"}
                            },
                            "required": ["executive_summary", "summary", "key_points", "insights", "risks", "opportunities"],
                            "additionalProperties": True
                        }
                    }

                    resp = from_responses_simple(
                        client=client,
                        model=os.getenv("AI_MODEL", "gpt-5"),
                        messages=[
                            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                            {"role": "user", "content": [{"type": "input_text", "text": f"Demande: {prompt}\n\nDONNÉES FACTUELLES (snapshot):\n{attempt_snapshot}\n\nDONNÉES COLLECTÉES (articles):\n{attempt_context}"}]}
                        ],
                        max_output_tokens=current_max_tokens,
                        reasoning_effort=os.getenv("AI_REASONING_EFFORT", "high"),
                        response_format={"type": "json_schema", "json_schema": json_schema}
                    )
                    raw = extract_output_text(resp) or ""
                    try:
                        logger.info(f"llm_raw_len={len(raw)} attempt={attempt+1}")
                        logger.debug(f"llm_raw_head={raw[:1000]}")
                    except Exception:
                        pass

                    # Validation stricte du schéma JSON
                    def validate_llm_response(data: dict) -> bool:
                        """Valide que la réponse LLM respecte le schéma attendu"""
                        if not isinstance(data, dict):
                            return False
                        
                        required_fields = ['executive_summary', 'summary', 'key_points']
                        for field in required_fields:
                            if field not in data:
                                logger.error(f"Champ manquant: {field}")
                                return False
                            if field in ['executive_summary', 'key_points'] and not isinstance(data[field], list):
                                logger.error(f"Champ {field} doit être une liste, reçu: {type(data[field])}")
                                return False
                            if field == 'summary' and not isinstance(data[field], str):
                                logger.error(f"Champ {field} doit être une string, reçu: {type(data[field])}")
                                return False
                        
                        # Vérifier que summary n'est pas du JSON stringifié
                        if isinstance(data.get('summary'), str) and data['summary'].strip().startswith('{'):
                            logger.error("Le champ 'summary' contient du JSON stringifié au lieu d'une string")
                            return False
                            
                        return True

                    # Parsing JSON robuste avec réparation automatique
                    def _safe_parse_json(text: str):
                        try:
                            s = (text or "").strip()
                            # retirer les fences ```json ... ``` si présents
                            s = re.sub(r"```\s*json\s*", "", s, flags=re.IGNORECASE)
                            s = s.replace('```', '').strip()
                            # retirer éventuel BOM
                            if s.startswith('\ufeff'):
                                s = s.lstrip('\ufeff')
                            # normaliser guillemets typographiques
                            trans = {ord('\u201c'): '"', ord('\u201d'): '"', ord('\u2019'): "'", ord('\u2013'): '-', ord('\u2014'): '-'}
                            s = s.translate(trans)
                            # supprimer virgules traînantes avant } ou ]
                            s = re.sub(r",(\s*[}\]])", r"\\1", s)
                            
                            # Tentative de parse direct
                            try:
                                parsed = json.loads(s)
                                if validate_llm_response(parsed):
                                    return parsed
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON malformé détecté: {e}")
                                
                                # Tentative de réparation automatique
                                repaired = _repair_json(s)
                                if repaired:
                                    try:
                                        parsed = json.loads(repaired)
                                        if validate_llm_response(parsed):
                                            logger.info("JSON réparé avec succès")
                                            return parsed
                                    except Exception as repair_error:
                                        logger.error(f"Échec de réparation JSON: {repair_error}")
                                
                                # Fallback: extraction de JSON partiel
                                partial_json = _extract_partial_json(s)
                                if partial_json:
                                    try:
                                        parsed = json.loads(partial_json)
                                        if validate_llm_response(parsed):
                                            logger.info("JSON partiel extrait avec succès")
                                            return parsed
                                    except Exception as partial_error:
                                        logger.error(f"Échec extraction JSON partiel: {partial_error}")
                            
                            logger.error("Impossible de parser le JSON, même avec réparation")
                            return None
                            
                        except Exception as e:
                            logger.error(f"Erreur parsing JSON: {e}")
                            return None

                    def _repair_json(json_str: str) -> str:
                        """Tente de réparer un JSON malformé"""
                        try:
                            # Réparer les chaînes non terminées
                            # Compter les guillemets pour détecter les chaînes non fermées
                            quote_count = 0
                            in_string = False
                            escape_next = False
                            repaired = []
                            
                            for i, char in enumerate(json_str):
                                if escape_next:
                                    repaired.append(char)
                                    escape_next = False
                                    continue
                                    
                                if char == '\\':
                                    repaired.append(char)
                                    escape_next = True
                                    continue
                                    
                                if char == '"' and not escape_next:
                                    in_string = not in_string
                                    quote_count += 1
                                
                                repaired.append(char)
                            
                            # Si on est encore dans une chaîne à la fin, la fermer
                            if in_string:
                                repaired.append('"')
                                logger.info("Chaîne non terminée détectée et fermée")
                            
                            # Réparer les accolades non fermées
                            open_braces = repaired.count('{')
                            close_braces = repaired.count('}')
                            if open_braces > close_braces:
                                repaired.extend(['}'] * (open_braces - close_braces))
                                logger.info(f"Ajout de {open_braces - close_braces} accolades fermantes")
                            open_brk = repaired.count('[')
                            close_brk = repaired.count(']')
                            if open_brk > close_brk:
                                repaired.extend([']'] * (open_brk - close_brk))
                                logger.info(f"Ajout de {open_brk - close_brk} crochets fermants")
                            
                            return ''.join(repaired)
                            
                        except Exception as e:
                            logger.error(f"Erreur lors de la réparation JSON: {e}")
                            return None

                    def _extract_partial_json(json_str: str) -> str:
                        """Extrait un JSON partiel valide depuis un JSON malformé"""
                        try:
                            # Chercher le premier objet JSON complet
                            depth = 0
                            start_idx = None
                            end_idx = None
                            
                            for i, char in enumerate(json_str):
                                if char == '{':
                                    if depth == 0:
                                        start_idx = i
                                    depth += 1
                                elif char == '}' and depth > 0:
                                    depth -= 1
                                    if depth == 0 and start_idx is not None:
                                        end_idx = i
                                        break
                            
                            if start_idx is not None and end_idx is not None:
                                partial = json_str[start_idx:end_idx + 1]
                                logger.info(f"Extraction JSON partiel: {len(partial)} caractères")
                                return partial
                            
                            return None
                            
                        except Exception as e:
                            logger.error(f"Erreur extraction JSON partiel: {e}")
                            return None

                    def _ensure_structured_data_mirror(obj: dict) -> dict:
                        """Complète automatiquement structured_data en copiant les 6 sections avancées.
                        Si structured_data est manquant/vide ou incomplet, on reconstruit à partir des sections racine.
                        """
                        try:
                            if not isinstance(obj, dict):
                                return obj
                            sections = [
                                "executive_dashboard",
                                "deep_analysis",
                                "quantitative_signals",
                                "risk_management",
                                "actionable_summary",
                                "economic_indicators",
                            ]
                            sd = obj.get("structured_data")
                            needs_build = not isinstance(sd, dict) or any(k not in sd for k in sections)
                            if needs_build:
                                mirrored = {}
                                for key in sections:
                                    if key in obj and obj.get(key) is not None:
                                        mirrored[key] = obj.get(key)
                                obj["structured_data"] = mirrored
                        except Exception:
                            # En cas d'erreur on ne bloque pas le flux
                            pass
                        return obj

                    parsed = _safe_parse_json(raw)
                    if parsed is None:
                        # Retry avec instruction de correction si tentative restante
                        if attempt < 2:
                            logger.info("Retry LLM avec instruction de correction JSON…")
                            correction_prompt = system_prompt + "\n\nATTENTION: La réponse précédente n'était pas un JSON valide. Renvoie le MÊME CONTENU sous forme d'un SEUL objet JSON complet et fermé, sans texte hors JSON."
                            resp = from_responses_simple(
                                client=client,
                                model=os.getenv("AI_MODEL", "gpt-5"),
                                messages=[
                                    {"role": "system", "content": [{"type": "input_text", "text": correction_prompt}]},
                                    {"role": "user", "content": [{"type": "input_text", "text": f"Demande: {prompt}\n\nDONNÉES FACTUELLES (snapshot):\n{attempt_snapshot}\n\nDONNÉES COLLECTÉES (articles):\n{attempt_context}"}]}
                                ],
                                max_output_tokens=current_max_tokens,
                                reasoning_effort=os.getenv("AI_REASONING_EFFORT", "high"),
                                response_format={"type": "json_schema", "json_schema": json_schema}
                            )
                            raw = extract_output_text(resp) or ""
                            parsed = _safe_parse_json(raw)
                        if parsed is None:
                            if strict_mode:
                                raise RuntimeError("LLM JSON invalide après réparations/retry (mode strict activé)")
                            # fallback structuré (mode non strict)
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

                    # Normaliser les champs attendus si manquants
                    if not isinstance(parsed.get("executive_summary"), list):
                        parsed["executive_summary"] = []
                    if not isinstance(parsed.get("key_points"), list):
                        parsed["key_points"] = []
                    if not isinstance(parsed.get("insights"), list):
                        parsed["insights"] = []
                    if not isinstance(parsed.get("risks"), list):
                        parsed["risks"] = []
                    if not isinstance(parsed.get("opportunities"), list):
                        parsed["opportunities"] = []
                    if parsed.get("summary") is None:
                        parsed["summary"] = ""

                    # Dériver un executive_summary minimal si vide
                    if not parsed["executive_summary"]:
                        if parsed["key_points"]:
                            parsed["executive_summary"] = parsed["key_points"][:10]
                        elif parsed["summary"]:
                            try:
                                sents = [p.strip() for p in str(parsed["summary"]).split('.') if p.strip()]
                                parsed["executive_summary"] = [x + '.' for x in sents[:8]]
                            except Exception:
                                parsed["executive_summary"] = []

                    # Assurer le miroir legacy automatiquement
                    parsed = _ensure_structured_data_mirror(parsed)

                    result = parsed
                    try:
                        if isinstance(result.get('sources'), list) and len(result['sources']) == 0:
                            logger.warning("⚠️ LLM a retourné 0 source dans le rapport")
                    except Exception:
                        pass
                    logger.info(f"✅ OpenAI a retourné une réponse complète (exec={len(result.get('executive_summary', []))}, key={len(result.get('key_points', []))}, summary_len={len(result.get('summary',''))})")
                    return result
                    
                except Exception as e:
                    err = str(e)
                    logger.warning(f"⚠️ Tentative {attempt + 1}/3 échouée: {err}")
                    # Gestion spécifique 429 (rate limit): réduire tokens et contexte, backoff adapté
                    if '429' in err or 'rate limit' in err.lower():
                        wait_seconds = 6.0
                        try:
                            m = re.search(r'try again in\s+([0-9\.]+)s', err, flags=re.IGNORECASE)
                            if m:
                                wait_seconds = float(m.group(1)) + 0.5
                        except Exception:
                            pass
                        # Réduire la charge pour la prochaine tentative
                        new_tokens = max(int(current_max_tokens * 0.8), 12000)
                        if new_tokens < current_max_tokens:
                            current_max_tokens = new_tokens
                        context_shrink *= 0.85
                        snapshot_shrink *= 0.85
                        logger.warning(f"🔧 Rate limit: next attempt with max_tokens={current_max_tokens}, context~{int(context_shrink*100)}%, snapshot~{int(snapshot_shrink*100)}%; wait {wait_seconds:.1f}s")
                        if attempt < 2:
                            await asyncio.sleep(wait_seconds)
                            continue
                        else:
                            raise
                    # Autres erreurs: backoff simple
                    if attempt < 2:
                        await asyncio.sleep(2)
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement LLM: {e}")
            if str(os.getenv('STRICT_LLM_JSON', '0')).strip() in ('1', 'true', 'True'):
                # Mode strict: remonter l'erreur pour annuler sauvegarde/email
                raise
            # Mode non strict: retourner un objet sûr
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
            
            # Scraping - Deep sur YF, MW, CNN uniquement (min 25k chars)
            min_chars = int(os.getenv('LLM_MIN_CONTEXT_CHARS', '25000'))
            scraped_data = await self.search_and_scrape_deep(task.prompt, per_site=12, max_age_hours=48, min_chars=min_chars)

            # X.com désactivé sur demande: pas d'enrichissement par tweets
            logger.info("🐦 X.com désactivé (pas d'intégration dans le scraping)")
            
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