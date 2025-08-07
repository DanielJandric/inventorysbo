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

class MarketAnalysisWorker:
    def __init__(self):
        self.scraper = get_scrapingbee_scraper()
        self.db = get_market_analysis_db()
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

        try:
            # 1. Mettre à jour le statut à "processing"
            self.db.update_analysis_status(task_id, 'processing')

            # 2. Exécuter le scraping et l'analyse LLM
            prompt = task.prompt or "Analyse générale des marchés financiers avec focus sur l'IA."
            
            scraper_task_id = await self.scraper.create_scraping_task(prompt, 3)
            result = await self.scraper.execute_scraping_task(scraper_task_id)

            # 3. Traiter le résultat
            if "error" in result:
                raise ValueError(result['error'])

            processing_time = int(time.time() - start_time)
            
            # 4. Mettre à jour la tâche avec les résultats complets
            update_data = {
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
            self.db.update_analysis(task_id, update_data)
            logger.info(f"✅ Tâche #{task_id} terminée avec succès en {processing_time}s.")

        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la tâche #{task_id}: {e}")
            processing_time = int(time.time() - start_time)
            self.db.update_analysis(task_id, {
                'worker_status': 'error',
                'error_message': str(e),
                'processing_time_seconds': processing_time
            })

    async def run_continuous_loop(self):
        """Boucle principale qui recherche et traite les tâches."""
        logger.info("🔄 Démarrage de la boucle de traitement des tâches...")
        while self.is_running:
            try:
                # Chercher une tâche en attente
                pending_task = self.db.get_pending_analysis()

                if pending_task:
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
        # Lancer les tâches en parallèle (analyses, immobilier, market brief)
        market_analysis_task = asyncio.create_task(worker.run_continuous_loop())
        real_estate_task = asyncio.create_task(worker.run_real_estate_scrape_periodically())
        market_brief_task = asyncio.create_task(worker.run_nightly_market_brief())
        await asyncio.gather(market_analysis_task, real_estate_task, market_brief_task)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Arrêt initié.")
    except Exception as e:
        logger.error(f"❌ Le worker s'est arrêté en raison d'une erreur fatale: {e}")
    finally:
        worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
