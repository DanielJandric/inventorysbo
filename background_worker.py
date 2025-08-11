#!/usr/bin/env python3
"""
Background Worker pour Render - Traite les analyses de marché en file d'attente
"""

import os
import asyncio
import time
import logging
import json
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Dict
from dotenv import load_dotenv

# Optional Redis cache
try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("--- DÉMARRAGE DU SCRIPT DU BACKGROUND WORKER ---")

# Imports
from scrapingbee_scraper import get_scrapingbee_scraper
from market_analysis_db import get_market_analysis_db, MarketAnalysis
from stock_api_manager import stock_api_manager
 

class MarketAnalysisWorker:
    def __init__(self):
        self.scraper = get_scrapingbee_scraper()
        self.db = get_market_analysis_db()
        # NewsAPI removed; ScrapingBee is the only source for analysis
        self.poll_interval_seconds = 15  # Vérifier les nouvelles tâches toutes les 15 secondes
        self.is_running = False
        self.redis_client = None
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialise Redis si disponible (facultatif)."""
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis and redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Ping pour valider la connexion
                self.redis_client.ping()
                logger.info("✅ Cache Redis initialisé")
            else:
                if not redis:
                    logger.info("ℹ️ Redis non installé, cache désactivé")
                elif not redis_url:
                    logger.info("ℹ️ REDIS_URL non défini, cache désactivé")
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'initialiser Redis: {e}")
            self.redis_client = None

    def initialize(self):
        """Initialise le worker et ses dépendances."""
        try:
            logger.info("🚀 Initialisation du Background Worker...")
            # Vérification des variables d'environnement
            required = ['SCRAPINGBEE_API_KEY', 'OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
            if any(not os.getenv(var) for var in required):
                raise ValueError(f"Variables d'environnement manquantes: {', '.join(v for v in required if not os.getenv(v))}")

            self.scraper.initialize_sync()
            if not self.db.is_connected():
                raise ConnectionError("Connexion à la base de données impossible.")
            
            self.is_running = True
            logger.info(f"✅ Worker prêt. Intervalle de vérification: {self.poll_interval_seconds}s")
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation fatale: {e}")
            raise

    async def process_task(self, task: MarketAnalysis):
        """Traite une seule tâche d'analyse."""
        start_time = time.time()
        task_id = task.id
        logger.info(f"📊 Prise en charge de la tâche #{task_id}...")
        logger.info(f"   - Type: {task.analysis_type}")
        logger.info(f"   - Prompt: {task.prompt[:100]}...")

        try:
            # 1. Mettre à jour le statut à "processing"
            logger.info(f"🔄 Mise à jour du statut de la tâche #{task_id} à 'processing'...")
            self.db.update_analysis_status(task_id, 'processing')

            # 2. Exécuter l'analyse (ScrapingBee uniquement)
            prompt = task.prompt or "Analyse générale des marchés financiers avec focus sur l'IA."
            logger.info(f"🕷️ Création de la tâche ScrapingBee avec prompt: {prompt[:100]}...")
            scraper_task_id = await self.scraper.create_scraping_task(prompt, 3)
            
            logger.info(f"🚀 Exécution de la tâche ScrapingBee {scraper_task_id}...")
            result = await self.scraper.execute_scraping_task(scraper_task_id)


            # 3. Traiter le résultat
            if "error" in result:
                logger.error(f"❌ Erreur reçue de ScrapingBee: {result['error']}")
                raise ValueError(result['error'])

            processing_time = int(time.time() - start_time)
            
            logger.info(f"📊 Résultats obtenus:")
            logger.info(f"   - Executive Summary: {len(result.get('executive_summary', []))} points")
            logger.info(f"   - Résumé: {len(result.get('summary', ''))} caractères")
            logger.info(f"   - Points clés: {len(result.get('key_points', []))} points")
            logger.info(f"   - Insights: {len(result.get('insights', []))} insights")
            logger.info(f"   - Sources: {len(result.get('sources', []))} sources")
            
            # 4. Mettre à jour la tâche avec les résultats complets
            update_data = {
                'executive_summary': result.get('executive_summary', []),
                'summary': result.get('summary'),
                'key_points': result.get('key_points', []),
                'structured_data': result.get('structured_data', {}),
                'insights': result.get('insights', []),
                'risks': result.get('risks', []),
                'opportunities': result.get('opportunities', []),
                'sources': result.get('sources', []),
                'confidence_score': result.get('confidence_score', 0.0),
                'worker_status': 'completed',
                'processing_time_seconds': processing_time
            }
            
            logger.info(f"💾 Sauvegarde des résultats dans la base de données...")
            self.db.update_analysis(task_id, update_data)
            logger.info(f"✅ Tâche #{task_id} terminée avec succès en {processing_time}s.")
            
            # 5. Envoyer le rapport par email (si configuré)
            await self._send_market_analysis_email(task_id, result)

        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la tâche #{task_id}: {e}")
            processing_time = int(time.time() - start_time)
            self.db.update_analysis(task_id, {
                'worker_status': 'error',
                'error_message': str(e),
                'processing_time_seconds': processing_time
            })

    async def _send_market_analysis_email(self, task_id: int, analysis_result: Dict):
        """Envoie le rapport d'analyse de marché par email."""
        try:
            # Vérifier la configuration email
            email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
            email_port = int(os.getenv("EMAIL_PORT", "587"))
            email_user = os.getenv("EMAIL_USER")
            email_password = os.getenv("EMAIL_PASSWORD")
            recipients = [e.strip() for e in os.getenv("EMAIL_RECIPIENTS", "").split(",") if e.strip()]
            
            if not (email_user and email_password and recipients):
                logger.info("ℹ️ Configuration email incomplète, pas d'envoi")
                return
            
            # Récupérer l'analyse complète depuis la DB
            analysis = self.db.get_analysis_by_id(task_id)
            if not analysis:
                logger.warning(f"⚠️ Impossible de récupérer l'analyse #{task_id} pour l'email")
                return
            
            # Préparer le contenu HTML
            html_content = self._generate_market_analysis_html(analysis, analysis_result)
            
            # Créer et envoyer l'email
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"[BONVIN] Rapport d'Analyse de Marché - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            with smtplib.SMTP(email_host, email_port) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.send_message(msg)
            
            logger.info(f"📧 Rapport d'analyse #{task_id} envoyé par email à {len(recipients)} destinataires")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email rapport #{task_id}: {e}")

    def _generate_market_analysis_html(self, analysis: 'MarketAnalysis', result: Dict) -> str:
        """Génère le contenu HTML pour l'email."""
        # Récupérer les données du snapshot de marché
        from stock_api_manager import stock_api_manager
        market_snapshot = stock_api_manager.get_market_snapshot()
        
        # Générer le HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 3px solid #1e3a8a; padding-bottom: 20px; margin-bottom: 30px; }}
                .header h1 {{ color: #1e3a8a; margin: 0; }}
                .header .date {{ color: #666; font-size: 14px; margin-top: 10px; }}
                .executive-summary {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .executive-summary h2 {{ margin-top: 0; color: #fbbf24; }}
                .executive-summary ul {{ margin: 0; padding-left: 20px; }}
                .executive-summary li {{ margin-bottom: 8px; font-size: 16px; }}
                .section {{ margin-bottom: 30px; }}
                .section h3 {{ color: #1e3a8a; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
                .market-snapshot {{ background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; }}
                .market-snapshot table {{ width: 100%; border-collapse: collapse; }}
                .market-snapshot th, .market-snapshot td {{ padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
                .market-snapshot th {{ background: #3b82f6; color: white; }}
                .insights {{ background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b; }}
                .risks {{ background: #fee2e2; padding: 20px; border-radius: 8px; border-left: 4px solid #ef4444; }}
                .opportunities {{ background: #dcfce7; padding: 20px; border-radius: 8px; border-left: 4px solid #22c55e; }}
                .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 RAPPORT D'ANALYSE DE MARCHÉ</h1>
                    <div class="date">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</div>
                </div>
                
                <!-- Executive Summary -->
                <div class="executive-summary">
                    <h2>🎯 EXECUTIVE SUMMARY</h2>
                    <ul>
                        {chr(10).join([f'<li>{point}</li>' for point in (result.get('executive_summary', []) or [])])}
                    </ul>
                </div>
                
                <!-- Résumé détaillé -->
                <div class="section">
                    <h3>📝 Résumé de l'Analyse</h3>
                    <p>{result.get('summary', 'Aucun résumé disponible')}</p>
                </div>
                
                <!-- Aperçu du marché -->
                <div class="section">
                    <h3>📈 Aperçu du Marché</h3>
                    <div class="market-snapshot">
                        <table>
                            <thead>
                                <tr><th>Actif</th><th>Prix</th><th>Variation</th><th>Source</th></tr>
                            </thead>
                            <tbody>
                                {self._generate_market_snapshot_rows(market_snapshot)}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Points clés -->
                <div class="section">
                    <h3>🔑 Points Clés</h3>
                    <ul>
                        {chr(10).join([f'<li>{point}</li>' for point in (result.get('key_points', []) or [])])}
                    </ul>
                </div>
                
                <!-- Insights -->
                <div class="insights">
                    <h3>💡 Insights</h3>
                    <ul>
                        {chr(10).join([f'<li>{insight}</li>' for insight in (result.get('insights', []) or [])])}
                    </ul>
                </div>
                
                <!-- Risques -->
                <div class="risks">
                    <h3>⚠️ Risques Identifiés</h3>
                    <ul>
                        {chr(10).join([f'<li>{risk}</li>' for insight in (result.get('risks', []) or [])])}
                    </ul>
                </div>
                
                <!-- Opportunités -->
                <div class="opportunities">
                    <h3>🚀 Opportunités</h3>
                    <ul>
                        {chr(10).join([f'<li>{opp}</li>' for opp in (result.get('opportunities', []) or [])])}
                    </ul>
                </div>
                
                <!-- Sources -->
                <div class="section">
                    <h3>📚 Sources</h3>
                    <ul>
                        {chr(10).join([f'<li><a href="{source.get("url", "#")}" target="_blank">{source.get("title", "Source")}</a></li>' for source in (result.get('sources', []) or [])])}
                    </ul>
                </div>
                
                <div class="footer">
                    <p>Rapport généré automatiquement par le système BONVIN Collection</p>
                    <p>Confiance: {result.get('confidence_score', 0) * 100:.1f}%</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def _generate_market_snapshot_rows(self, snapshot: Dict) -> str:
        """Génère les lignes du tableau de snapshot de marché."""
        rows = []
        
        if snapshot.get('indices'):
            rows.append('<tr><td colspan="4" style="background: #e5e7eb; font-weight: bold; padding: 10px;">Indices</td></tr>')
            for name, data in snapshot['indices'].items():
                change_color = 'green' if data.get('change', 0) >= 0 else 'red'
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>{data.get('price', 'N/A')}</td>
                        <td style="color: {change_color}">{data.get('change', 'N/A')} ({data.get('change_percent', 'N/A')}%)</td>
                        <td>yfinance</td>
                    </tr>
                ''')
        
        if snapshot.get('commodities'):
            rows.append('<tr><td colspan="4" style="background: #e5e7eb; font-weight: bold; padding: 10px;">Matières Premières</td></tr>')
            for name, data in snapshot['commodities'].items():
                change_color = 'green' if data.get('change', 0) >= 0 else 'red'
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>{data.get('price', 'N/A')}</td>
                        <td style="color: {change_color}">{data.get('change', 'N/A')} ({data.get('change_percent', 'N/A')}%)</td>
                        <td>yfinance</td>
                    </tr>
                ''')
        
        if snapshot.get('crypto'):
            rows.append('<tr><td colspan="4" style="background: #e5e7eb; font-weight: bold; padding: 10px;">Cryptomonnaies</td></tr>')
            for name, data in snapshot['crypto'].items():
                change_color = 'green' if data.get('change', 0) >= 0 else 'red'
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>{data.get('price', 'N/A')}</td>
                        <td style="color: {change_color}">{data.get('change', 'N/A')} ({data.get('change_percent', 'N/A')}%)</td>
                        <td>yfinance</td>
                    </tr>
                ''')
        
        return chr(10).join(rows) if rows else '<tr><td colspan="4">Aucune donnée disponible</td></tr>'

    # NewsAPI analysis path removed

    async def run_continuous_loop(self):
        """Boucle principale qui recherche et traite les tâches."""
        logger.info("🔄 Démarrage de la boucle de traitement des tâches...")
        check_count = 0
        while self.is_running:
            try:
                check_count += 1
                if check_count % 20 == 1:  # Log toutes les 5 minutes environ
                    logger.info(f"👀 Vérification #{check_count} des tâches en attente...")
                
                # Chercher une tâche en attente
                pending_task = self.db.get_pending_analysis()

                if pending_task:
                    logger.info(f"🎯 Tâche trouvée! ID: {pending_task.id}, Type: {pending_task.analysis_type}")
                    await self.process_task(pending_task)
                else:
                    # Pas de tâche, on attend avant de vérifier à nouveau
                    await asyncio.sleep(self.poll_interval_seconds)

            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle principale: {e}")
                await asyncio.sleep(60) # Attendre plus longtemps en cas d'erreur grave

    async def run_real_estate_scrape_periodically(self):
        """Lance le scraping immobilier à intervalle régulier."""
        logger.info("🏡 Démarrage du scraping immobilier périodique...")
        while self.is_running:
            try:
                # Importation de la fonction principale du nouveau scraper
                from real_estate_scraper import run_real_estate_scraper
                
                logger.info("Lancement de la tâche de scraping immobilier...")
                await run_real_estate_scraper()
                
                # Attendre 6 heures avant le prochain cycle
                logger.info("Tâche de scraping immobilier terminée. Prochain cycle dans 6 heures.")
                await asyncio.sleep(6 * 3600)

            except Exception as e:
                logger.error(f"❌ Erreur critique dans le scraping immobilier périodique: {e}")
                await asyncio.sleep(3600) # Réessayer dans 1 heure en cas d'erreur


    # ──────────────────────────────────────────────────────────
    #  Seeking Alpha nightly market brief (summary + movers + news)
    # ──────────────────────────────────────────────────────────
    async def run_nightly_market_brief(self):
        """Génère un briefing de marché tous les jours à l'heure configurée."""
        logger.info("📰 Démarrage du job nocturne Market Brief...")
        target_time = os.getenv("MARKET_BRIEF_TIME", "21:30")  # HH:MM Europe/Paris
        region = os.getenv("MARKET_BRIEF_REGION", "US")

        while self.is_running:
            try:
                # Calculer le délai jusqu'au prochain créneau (Europe/Paris)
                now_utc = datetime.now(timezone.utc)
                # décalage approximatif Paris (gère DST grossièrement via time.localtime offset si dispo)
                paris_offset_minutes = 120  # fallback CET/CEST; pour précision, utiliser zoneinfo
                try:
                    # tentative d'ajustement simple via time.localtime (non fiable sur serveur UTC)
                    pass
                except Exception:
                    pass

                hh, mm = [int(x) for x in target_time.split(":")]
                today_paris = now_utc + timedelta(minutes=paris_offset_minutes)
                next_run_paris = today_paris.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if next_run_paris <= today_paris:
                    next_run_paris += timedelta(days=1)
                sleep_seconds = int((next_run_paris - today_paris).total_seconds())
                logger.info(f"🕙 Prochain Market Brief dans ~{sleep_seconds//60} min")
                await asyncio.sleep(max(30, sleep_seconds))

                # Exécuter le brief
                await self._execute_market_brief(region)

                # Attendre 60s pour éviter double exécution si boucle rapide
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"❌ Erreur Market Brief loop: {e}")
                await asyncio.sleep(600)

    async def _execute_market_brief(self, region: str) -> None:
        """Récupère les données Seeking Alpha, les agrège, sauvegarde et envoie un email."""
        logger.info("🧩 Génération du Market Brief (Seeking Alpha)...")
        from seeking_alpha_manager import (
            get_movers as sa_get_movers,
            get_news as sa_get_news,
            get_market_summary as sa_get_summary,
        )

        # Helper cache + retry
        async def fetch_cached_json(cache_key: str, ttl: int, caller, *args, **kwargs):
            # Cache Redis
            if self.redis_client:
                try:
                    cached = self.redis_client.get(cache_key)
                    if cached:
                        return json.loads(cached)
                except Exception:
                    pass
            # Retry with backoff
            delay = 1
            for attempt in range(4):
                try:
                    data = caller(*args, **kwargs)
                    if data:
                        if self.redis_client:
                            try:
                                self.redis_client.setex(cache_key, ttl, json.dumps(data))
                            except Exception:
                                pass
                        return data
                except Exception as e:
                    logger.warning(f"Tentative {attempt+1} échouée pour {cache_key}: {e}")
                await asyncio.sleep(delay)
                delay *= 2
            return None

        movers = await fetch_cached_json(f"sa:movers:{region}", 600, sa_get_movers, region)
        summary = await fetch_cached_json(f"sa:summary:{region}", 600, sa_get_summary, region)
        news = await fetch_cached_json("sa:news", 600, sa_get_news)

        # Construire le contenu texte simple
        now_paris = datetime.utcnow() + timedelta(minutes=120)
        date_str = now_paris.strftime("%Y-%m-%d")
        time_str = now_paris.strftime("%H:%M")

        def take_list(d, key):
            arr = (d or {}).get("data") if isinstance(d, dict) else None
            return arr if isinstance(arr, list) else []

        movers_list = take_list(movers, "data") or take_list(movers, "result")
        news_list = take_list(news, "data") or take_list(news, "result")

        lines = [
            f"Rapport de Marché - {date_str} {time_str} (région {region})",
            "",
            "Résumé marché:",
        ]
        if isinstance(summary, dict):
            lines.append(json.dumps(summary.get("result") or summary.get("data") or summary, ensure_ascii=False)[:800])
        lines += ["", "Top movers:"]
        for item in (movers_list or [])[:10]:
            sym = item.get("symbol") or item.get("ticker") or item.get("name", "?")
            pct = item.get("changesPercentage") or item.get("pctChange")
            last = item.get("last") or item.get("price")
            lines.append(f" - {sym}: {pct} | {last}")
        lines += ["", "News principales:"]
        for n in (news_list or [])[:8]:
            title = n.get("title") or n.get("headline")
            url = n.get("url") or n.get("link") or "#"
            lines.append(f" - {title} - {url}")

        content = "\n".join(lines)

        # Enregistrer dans market_updates via Supabase
        try:
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                sb = create_client(supabase_url, supabase_key)
                sb.table("market_updates").insert({
                    "content": content,
                    "date": date_str,
                    "time": time_str,
                    "trigger_type": "scheduled"
                }).execute()
                logger.info("✅ Market Brief sauvegardé dans market_updates")
            else:
                logger.warning("⚠️ Supabase non configuré, Market Brief non sauvegardé")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde Market Brief: {e}")

        # Envoyer l'email digest (si configuré)
        try:
            email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
            email_port = int(os.getenv("EMAIL_PORT", "587"))
            email_user = os.getenv("EMAIL_USER")
            email_password = os.getenv("EMAIL_PASSWORD")
            recipients = [e.strip() for e in os.getenv("EMAIL_RECIPIENTS", "").split(",") if e.strip()]
            if email_user and email_password and recipients:
                msg = MIMEMultipart('alternative')
                msg['From'] = email_user
                msg['To'] = ", ".join(recipients)
                msg['Subject'] = f"[BONVIN] Daily Market Brief - {date_str}"
                html = f"""
                <html><body>
                <h2>Daily Market Brief ({region})</h2>
                <pre style='font-family:Inter,Arial,sans-serif; white-space:pre-wrap'>{content}</pre>
                </body></html>
                """
                msg.attach(MIMEText(html, 'html', 'utf-8'))
                with smtplib.SMTP(email_host, email_port) as server:
                    server.starttls()
                    server.login(email_user, email_password)
                    server.send_message(msg)
                logger.info("📧 Market Brief envoyé par email")
            else:
                logger.info("ℹ️ Email non configuré, pas d'envoi de brief")
        except Exception as e:
            logger.error(f"❌ Erreur envoi email Market Brief: {e}")

    # ──────────────────────────────────────────────────────────
    #  Stock prices refresh (own currency, no conversion)
    # ──────────────────────────────────────────────────────────
    async def run_stock_prices_refresh_schedule(self):
        """Met à jour périodiquement les prix des actions (sans conversion)."""
        logger.info("📈 Démarrage du job périodique de mise à jour des prix d'actions...")
        times_csv = os.getenv("STOCK_REFRESH_TIMES", "09:00,11:00,13:00,15:00,17:00,21:30")
        times = [t.strip() for t in times_csv.split(",") if t.strip()]
        while self.is_running:
            try:
                # Prochain créneau (approx Europe/Paris +120m)
                now_utc = datetime.now(timezone.utc)
                today_paris = now_utc + timedelta(minutes=120)
                next_runs = []
                for t in times:
                    try:
                        hh, mm = [int(x) for x in t.split(":")]
                        nr = today_paris.replace(hour=hh, minute=mm, second=0, microsecond=0)
                        if nr <= today_paris:
                            nr += timedelta(days=1)
                        next_runs.append(nr)
                    except Exception:
                        continue
                if not next_runs:
                    await asyncio.sleep(3600)
                    continue
                next_run_paris = min(next_runs)
                sleep_seconds = int((next_run_paris - today_paris).total_seconds())
                logger.info(f"🕒 Prochaine MAJ prix actions dans ~{max(0, sleep_seconds)//60} min")
                await asyncio.sleep(max(30, sleep_seconds))

                # Exécuter la mise à jour
                await self._refresh_all_stocks()
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"❌ Erreur loop MAJ actions: {e}")
                await asyncio.sleep(600)

    async def _refresh_all_stocks(self):
        """Rafraîchit tous les prix d'actions via StockAPIManager et sauvegarde dans Supabase."""
        try:
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if not (supabase_url and supabase_key):
                logger.warning("⚠️ Supabase non configuré, MAJ des prix ignorée")
                return
            sb = create_client(supabase_url, supabase_key)

            resp = sb.table('items').select('*').eq('category', 'Actions').execute()
            rows = resp.data or []
            if not rows:
                logger.info("ℹ️ Aucune action à mettre à jour")
                return
            updated = 0
            failed = 0
            for row in rows:
                symbol = row.get('stock_symbol')
                if not symbol:
                    continue
                try:
                    data = stock_api_manager.get_stock_price(symbol, force_refresh=True)
                    if not data or not data.get('price'):
                        failed += 1
                        continue
                    price = data.get('price')
                    qty = row.get('stock_quantity') or 1
                    update_data = {
                        'current_price': price,
                        'current_value': price * qty,
                        'last_price_update': datetime.utcnow().isoformat(),
                        'stock_volume': data.get('volume'),
                        'stock_pe_ratio': data.get('pe_ratio'),
                        'stock_52_week_high': data.get('fifty_two_week_high'),
                        'stock_52_week_low': data.get('fifty_two_week_low'),
                        'stock_change': data.get('change'),
                        'stock_change_percent': data.get('change_percent'),
                        'stock_average_volume': data.get('volume'),
                        'stock_currency': data.get('currency')
                    }
                    sb.table('items').update(update_data).eq('id', row['id']).execute()
                    updated += 1
                except Exception as e:
                    logger.warning(f"⚠️ Echec MAJ {symbol}: {e}")
                    failed += 1
            logger.info(f"✅ MAJ prix actions terminée: {updated} ok, {failed} échecs")
        except Exception as e:
            logger.error(f"❌ Erreur _refresh_all_stocks: {e}")


    def stop(self):
        """Arrête proprement le worker."""
        logger.info("🛑 Arrêt du Background Worker...")
        self.is_running = False
        if hasattr(self.scraper, 'cleanup'):
            self.scraper.cleanup()

async def main():
    """Point d'entrée principal."""
    worker = MarketAnalysisWorker()
    try:
        worker.initialize()
        # Lancer uniquement la file d'analyses marché (pas de tâches auto)
        market_analysis_task = asyncio.create_task(worker.run_continuous_loop())
        await asyncio.gather(market_analysis_task)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Arrêt initié.")
    except Exception as e:
        logger.error(f"❌ Le worker s'est arrêté en raison d'une erreur fatale: {e}")
    finally:
        worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
