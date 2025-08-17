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
            search_results = await self._search_google(query, max(num_results, 12))
            
            if not search_results:
                logger.warning("⚠️ Aucun résultat de recherche trouvé")
                return results
            
            # Étape 2: Scraping des pages avec ScrapingBee
            for i, result in enumerate(search_results[:max(num_results, 12)]):
                try:
                    logger.info(f"📖 Scraping {i+1}/{min(len(search_results), max(num_results, 12))}: {result['title']}")
                    
                    scraped = await self._scrape_page(result['url'])
                    
                    if scraped:
                        content = scraped.get('content') if isinstance(scraped, dict) else str(scraped)
                        published_at = scraped.get('published_at') if isinstance(scraped, dict) else None
                        results.append(ScrapedData(
                            url=result['url'],
                            title=result['title'],
                            content=content,
                            timestamp=published_at or datetime.now(),
                            metadata={
                                'word_count': len(content.split()),
                                'published_at': (published_at.isoformat() if published_at else None),
                                'source': 'scrapingbee'
                            }
                        ))
                    
                except Exception as e:
                    logger.error(f"❌ Erreur scraping {result['url']}: {e}")
                    results.append(ScrapedData(
                        url=result['url'],
                        title=result['title'],
                        content=f"Erreur lors du scraping: {str(e)}",
                        timestamp=datetime.now(),
                        metadata={'error': str(e), 'source': 'scrapingbee'}
                    ))
            
            # Prioriser les articles récents (quelque soit la source)
            results.sort(key=lambda r: r.timestamp or datetime.min, reverse=True)
            results = results[:max(num_results, 12)]
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche/scraping: {e}")
        
        return results
    
    async def _search_google(self, query: str, num_results: int = 5) -> List[Dict]:
        """Recherche sur des sites financiers directs avec ScrapingBee"""
        try:
            q = query.lower()
            # Listes de domaines FR/CH/UK
            fr_sources = [
                ("https://www.lesechos.fr/", "Les Echos"),
                ("https://www.lefigaro.fr/finance/", "Le Figaro Finance"),
                ("https://www.boursorama.com/", "Boursorama"),
                ("https://www.zonebourse.com/", "Zonebourse"),
            ]
            ch_sources = [
                ("https://www.letemps.ch/economie", "Le Temps - Economie"),
                ("https://www.rts.ch/info/economie/", "RTS - Economie"),
                ("https://www.swissinfo.ch/fre/economie", "SWI - Economie"),
            ]
            uk_us_sources = [
                ("https://www.reuters.com/markets/", "Reuters - Markets"),
                ("https://www.ft.com/markets", "FT - Markets"),
                ("https://www.bloomberg.com/markets", "Bloomberg - Markets"),
                ("https://www.cnbc.com/markets/", "CNBC - Markets"),
                ("https://www.marketwatch.com/", "MarketWatch"),
            ]

            sources: List[Dict[str, str]] = []
            # Prioriser FR/CH puis UK/US
            for url, title in fr_sources + ch_sources + uk_us_sources:
                sources.append({'url': url, 'title': title})
            
            logger.info(f"🔍 Sélection de {min(len(sources), num_results)} sources FR/CH/UK prioritaires")
            return sources[:num_results]
        except Exception as e:
            logger.error(f"❌ Erreur recherche sites financiers: {e}")
            return []
    
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
    

    
    def _extract_published_datetime(self, html_content: str, headers: Dict[str, str]) -> Optional[datetime]:
        """Essaie d'extraire la date de publication depuis HTML/meta ou headers."""
        try:
            # 1) Meta tags courants
            patterns = [
                r'property=["\']article:published_time["\']\s+content=["\']([^"\']+)["\']',
                r'property=["\']og:updated_time["\']\s+content=["\']([^"\']+)["\']',
                r'itemprop=["\']datePublished["\']\s+content=["\']([^"\']+)["\']',
                r'name=["\']date["\']\s+content=["\']([^"\']+)["\']',
                r'name=["\']pubdate["\']\s+content=["\']([^"\']+)["\']',
            ]
            for pat in patterns:
                m = re.search(pat, html_content, flags=re.IGNORECASE)
                if m:
                    val = m.group(1)
                    try:
                        # ISO 8601 simple
                        v = val.replace('Z', '+00:00')
                        return datetime.fromisoformat(v)
                    except Exception:
                        # YYYY-MM-DD HH:MM(:SS)?
                        m2 = re.search(r'(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)', val)
                        if m2:
                            try:
                                v2 = m2.group(1).replace(' ', 'T')
                                return datetime.fromisoformat(v2)
                            except Exception:
                                pass
            # 2) JSON-LD script
            mld = re.search(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_content, flags=re.IGNORECASE|re.DOTALL)
            if mld:
                try:
                    import json as _json
                    data = _json.loads(mld.group(1))
                    if isinstance(data, dict):
                        val = data.get('datePublished') or data.get('dateModified')
                        if isinstance(val, str):
                            v = val.replace('Z', '+00:00')
                            return datetime.fromisoformat(v)
                except Exception:
                    pass
            # 3) Header Last-Modified
            if headers:
                lm = headers.get('Last-Modified') or headers.get('last-modified')
                if lm:
                    try:
                        from email.utils import parsedate_to_datetime
                        return parsedate_to_datetime(lm)
                    except Exception:
                        pass
        except Exception:
            return None
        return None

    async def _scrape_page(self, url: str) -> Optional[Dict[str, object]]:
        """Scrape une page avec ScrapingBee et retourne contenu + date publiée si trouvée."""
        try:
            params = {
                'api_key': self.api_key,
                'url': url,
                'render_js': 'true',
                'premium_proxy': 'true',
                'block_resources': 'false',
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        cleaned_content = self._extract_text_from_html(html_content)
                        pub_dt = self._extract_published_datetime(html_content, dict(response.headers))
                        return {"content": cleaned_content[:12000], "published_at": pub_dt}
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
            # Troncature protectrice pour respecter budgets token
            try:
                max_ctx_chars = int(os.getenv('SCRAPER_MAX_CONTEXT_CHARS', '70000'))
            except Exception:
                max_ctx_chars = 70000
            if len(context) > max_ctx_chars:
                context = context[:max_ctx_chars]
                logger.info(f"🧠 Contexte tronqué à {max_ctx_chars} caractères pour limiter les tokens.")
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

MODE JSON STRICT: activé.
Output ONLY the JSON object. Do not include any accompanying text. No code fences, no commentary, no markdown.
"""
            system_prompt = system_prompt.strip() + "\n\nMODE JSON STRICT: activé.\nOutput ONLY the JSON object. Do not include any accompanying text. No code fences, no commentary, no markdown."
            
            chosen_model = os.getenv("AI_MODEL", "gpt-5")
            logger.info(f"🤖 Appel à l'API OpenAI ({chosen_model}) en cours pour une analyse exhaustive (prompt renforcé)...")
            
            # Essayer jusqu'à 3 fois en cas d'erreur
            for attempt in range(5):
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

                    # Token budget for output
                    try:
                        max_out_tokens = int(os.getenv('SCRAPER_MAX_OUTPUT_TOKENS', '25000'))
                    except Exception:
                        max_out_tokens = 25000

                    # Structured outputs: JSON Schema strict (fallback to JSON Mode)
                    schema = {
                        "type": "object",
                        "properties": {
                            "executive_summary": {"type": "array", "items": {"type": "string"}, "minItems": 10},
                            "summary": {"type": "string", "minLength": 2500},
                            "key_points": {"type": "array", "items": {"type": "string"}, "minItems": 12},
                            "structured_data": {"type": "object"},
                            "insights": {"type": "array", "items": {"type": "string"}},
                            "risks": {"type": "array", "items": {"type": "string"}},
                            "opportunities": {"type": "array", "items": {"type": "string"}},
                            "sources": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "url": {"type": "string", "format": "uri"}}, "required": ["title","url"], "additionalProperties": False}},
                            "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                        },
                        "required": ["executive_summary","summary","key_points","structured_data","sources","confidence_score"],
                        "additionalProperties": True
                    }

                    try:
                        resp = client.responses.create(
                            model=os.getenv("AI_MODEL", "gpt-5"),
                            input=input_messages,
                            response_format={
                                "type": "json_schema",
                                "json_schema": {"name": "research_report", "schema": schema, "strict": True}
                            },
                            temperature=0,
                            max_output_tokens=max_out_tokens,
                            reasoning={"effort": "high"}
                        )
                    except Exception:
                        # Fallback: JSON Mode
                        resp = client.responses.create(
                            model=os.getenv("AI_MODEL", "gpt-5"),
                            input=input_messages,
                            response_format={"type": "json_object"},
                            temperature=0,
                            max_output_tokens=max_out_tokens,
                            reasoning={"effort": "high"}
                        )

                    raw = getattr(resp, "output_text", None) or extract_output_text(resp) or ""
                    result = json.loads(raw)
                    logger.info(f"✅ OpenAI a retourné une réponse JSON valide")
                    return result
                    
                except Exception as e:
                    import random, re as _re
                    msg = str(e)
                    logger.warning(f"⚠️ Tentative {attempt + 1}/5 échouée: {msg}")
                    # Exponential backoff + respect de 'try again in Xs'
                    base_wait = 2 * (2 ** attempt)
                    m = _re.search(r"try again in ([0-9.]+)s", msg)
                    if m:
                        try:
                            hinted = float(m.group(1))
                            base_wait = max(base_wait, hinted + random.uniform(0.5, 1.5))
                        except Exception:
                            pass
                    if attempt < 4:
                        await asyncio.sleep(min(base_wait, 20))
                        # réduire la sortie demandée pour soulager le TPM
                        try:
                            new_limit = max(2000, int(max_out_tokens * 0.7))
                            os.environ['SCRAPER_MAX_OUTPUT_TOKENS'] = str(new_limit)
                            logger.info(f"🔧 SCRAPER_MAX_OUTPUT_TOKENS réduit à {new_limit}")
                        except Exception:
                            pass
                        continue
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