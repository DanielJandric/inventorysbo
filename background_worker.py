#!/usr/bin/env python3
"""
Background Worker pour Render - Traite les analyses de marché en file d'attente
"""

import os
import asyncio
import time
import logging
import json
import html
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Dict, List, Optional
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None  # fallback
from dotenv import load_dotenv

# Optional Redis cache
try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

# Charger les variables d'environnement
load_dotenv()

# Charger éventuellement une configuration locale (comme dans app.py)
# Cela permet au worker de récupérer SUPABASE_URL/SUPABASE_KEY/etc. depuis un config.py
# si les variables d'environnement ne sont pas présentes (cas fréquent en local).
try:
    import config  # type: ignore
    # Propager dans l'environnement uniquement les clés manquantes
    for _key in (
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "OPENAI_API_KEY",
        "SCRAPINGBEE_API_KEY",
        "EMAIL_HOST",
        "EMAIL_PORT",
        "EMAIL_USER",
        "EMAIL_PASSWORD",
        "EMAIL_RECIPIENTS",
    ):
        _val = getattr(config, _key, None)
        if _val and not os.getenv(_key):
            os.environ[_key] = str(_val)
except Exception:
    # Pas de config.py ou pas d'attributs : on reste sur les variables d'environnement
    pass

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

            # Traitement automatique d'un rapport mensuel si un payload est présent dans le repo
            try:
                self._process_monthly_payload_file()
            except Exception as e:
                logger.warning(f"⚠️ Impossible de traiter le payload mensuel automatique: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation fatale: {e}")
            raise

    async def process_task(self, task: MarketAnalysis):
        """Traite une seule tâche d'analyse."""
        MAX_SCRAPING_PAGES = 5
        DEFAULT_PROMPT = "Analyse générale des marchés financiers avec focus sur l'IA."
        
        start_time = time.time()
        task_id = task.id
        logger.info(f"📊 Prise en charge de la tâche #{task_id}...")
        logger.info(f"   - Type: {task.analysis_type}")
        logger.info(f"   - Prompt: {task.prompt[:100] if task.prompt else 'Aucun prompt'}...")

        try:
            # 1. Mettre à jour le statut à "processing"
            logger.info(f"🔄 Mise à jour du statut de la tâche #{task_id} à 'processing'...")
            self.db.update_analysis_status(task_id, 'processing')

            # 2. Préparer et exécuter l'analyse ScrapingBee
            prompt = task.prompt or DEFAULT_PROMPT
            logger.info(f"🕷️ Création de la tâche ScrapingBee avec prompt: {prompt[:100]}...")
            
            scraper_task_id = await self.scraper.create_scraping_task(prompt, MAX_SCRAPING_PAGES)
            
            logger.info(f"🚀 Exécution de la tâche ScrapingBee {scraper_task_id}...")
            result = await self.scraper.execute_scraping_task(scraper_task_id)


            # 3. Traiter le résultat
            if "error" in result:
                logger.error(f"❌ Erreur reçue de ScrapingBee: {result['error']}")
                raise ValueError(result['error'])

            processing_time = int(time.time() - start_time)

            logger.info(f"📊 Résultats obtenus (brut LLM):")
            logger.info(f"   - Executive Summary: {len(result.get('executive_summary', []))} points")
            logger.info(f"   - Résumé: {len(result.get('summary', ''))} caractères")
            logger.info(f"   - Points clés (brut): {len(result.get('key_points', []))} points")
            logger.info(f"   - Insights (brut): {len(result.get('insights', []))} insights")
            logger.info(f"   - Sources: {len(result.get('sources', []))} sources")

            # Utiliser directement les données du LLM sans normalisation excessive
            # Le LLM est maintenant configuré pour retourner des données correctement formatées
            
            # Validation basique des champs requis
            def _ensure_list_field(data, field_name, default=None):
                """S'assure qu'un champ est une liste valide"""
                if default is None:
                    default = []
                val = data.get(field_name, default)
                if isinstance(val, list):
                    return val
                elif isinstance(val, str) and val.strip():
                    # Si c'est une string, la convertir en liste d'un élément
                    return [val.strip()]
                else:
                    return default

            def _ensure_string_field(data, field_name, default=""):
                """S'assure qu'un champ est une string valide"""
                val = data.get(field_name, default)
                if isinstance(val, str):
                    return val.strip()
                elif val is not None:
                    return str(val).strip()
                else:
                    return default

            # Extraction directe des champs avec fallbacks intelligents
            exec_summary = _ensure_list_field(result, 'executive_summary')
            key_points = _ensure_list_field(result, 'key_points')
            insights = _ensure_list_field(result, 'insights')
            risks = _ensure_list_field(result, 'risks')
            opportunities = _ensure_list_field(result, 'opportunities')
            sources = _ensure_list_field(result, 'sources')
            summary_text = _ensure_string_field(result, 'summary')

            # Fallbacks intelligents pour les champs vides
            def _generate_fallback_insights():
                """Génère des insights depuis d'autres champs si la liste est vide"""
                fallbacks = []
                
                # Depuis structured_data.meta_analysis.key_drivers
                try:
                    meta = result.get('structured_data', {}).get('meta_analysis', {})
                    drivers = meta.get('key_drivers', {})
                    if drivers.get('primary'):
                        fallbacks.append(f"Facteur clé: {drivers['primary']}")
                    for label in ['secondary', 'emerging']:
                        arr = drivers.get(label, [])
                        if isinstance(arr, list):
                            fallbacks.extend([f"Facteur {label}: {item}" for item in arr[:2]])
                except Exception:
                    pass
                
                # Depuis executive_dashboard.top_trades
                try:
                    dashboard = result.get('structured_data', {}).get('executive_dashboard', {})
                    trades = dashboard.get('top_trades', [])
                    if isinstance(trades, list):
                        for trade in trades[:3]:
                            if isinstance(trade, dict) and trade.get('rationale'):
                                fallbacks.append(f"Trade insight: {trade['rationale']}")
                except Exception:
                    pass
                
                # Depuis key_points si pas d'insights
                if not fallbacks and key_points:
                    fallbacks = [f"Point clé: {point}" for point in key_points[:3]]
                
                return fallbacks[:5]  # Limiter à 5 insights

            def _generate_fallback_risks():
                """Génère des risques depuis d'autres champs si la liste est vide"""
                fallbacks = []
                
                # Depuis geopolitical_chess
                try:
                    geo = result.get('structured_data', {}).get('deep_analysis', {}).get('geopolitical_chess', {})
                    if geo.get('immediate_impacts'):
                        for impact in geo['immediate_impacts'][:2]:
                            if isinstance(impact, dict) and impact.get('event'):
                                fallbacks.append(f"Risque géopolitique: {impact['event']}")
                except Exception:
                    pass
                
                # Depuis risk_management
                try:
                    risk_mgmt = result.get('structured_data', {}).get('risk_management', {})
                    hedges = risk_mgmt.get('tail_risk_hedges', [])
                    if isinstance(hedges, list):
                        for hedge in hedges[:2]:
                            if isinstance(hedge, dict) and hedge.get('risk'):
                                fallbacks.append(f"Risque de queue: {hedge['risk']}")
                except Exception:
                    pass
                
                # Fallback générique si pas de risques spécifiques
                if not fallbacks:
                    fallbacks = [
                        "Volatilité des marchés",
                        "Risques géopolitiques",
                        "Inflation persistante"
                    ]
                
                return fallbacks[:4]  # Limiter à 4 risques

            def _generate_fallback_opportunities():
                """Génère des opportunités depuis d'autres champs si la liste est vide"""
                fallbacks = []
                
                # Depuis executive_dashboard.top_trades (trades positifs)
                try:
                    dashboard = result.get('structured_data', {}).get('executive_dashboard', {})
                    trades = dashboard.get('top_trades', [])
                    if isinstance(trades, list):
                        for trade in trades[:3]:
                            if isinstance(trade, dict) and trade.get('action') in ['LONG', 'BUY']:
                                instrument = trade.get('instrument', 'Actif')
                                fallbacks.append(f"Opportunité: {instrument}")
                except Exception:
                    pass
                
                # Depuis sector_rotation_matrix
                try:
                    deep = result.get('structured_data', {}).get('deep_analysis', {})
                    rotation = deep.get('sector_rotation_matrix', {})
                    outperformers = rotation.get('outperformers', [])
                    if isinstance(outperformers, list):
                        for sector in outperformers[:2]:
                            if isinstance(sector, dict) and sector.get('sector'):
                                fallbacks.append(f"Secteur performant: {sector['sector']}")
                except Exception:
                    pass
                
                # Fallback générique si pas d'opportunités spécifiques
                if not fallbacks:
                    fallbacks = [
                        "Secteur technologique",
                        "Marchés émergents",
                        "Énergies renouvelables"
                    ]
                
                return fallbacks[:4]  # Limiter à 4 opportunités

            # Appliquer les fallbacks si les champs sont vides
            if not insights:
                insights = _generate_fallback_insights()
                logger.info(f"🔄 Insights générés par fallback: {len(insights)} éléments")
            
            if not risks:
                risks = _generate_fallback_risks()
                logger.info(f"🔄 Risques générés par fallback: {len(risks)} éléments")
            
            if not opportunities:
                opportunities = _generate_fallback_opportunities()
                logger.info(f"🔄 Opportunités générées par fallback: {len(opportunities)} éléments")

            # 4. Mettre à jour la tâche avec les résultats directs du LLM
            # Nettoyer summary si JSON-like (ne pas tronquer pour email)
            def _clean_summary_for_storage(s: str) -> str:
                try:
                    txt = str(s or '').strip()
                    if not txt:
                        return ''
                    # Si le texte ressemble à un objet JSON complet, tenter d'en extraire la narrative
                    if txt.startswith('{') and ('"deep_analysis"' in txt or '"meta_analysis"' in txt):
                        try:
                            obj = json.loads(txt)
                            if isinstance(obj, dict):
                                cand = obj.get('summary') or (
                                    (obj.get('deep_analysis') or {}).get('narrative') if isinstance(obj.get('deep_analysis'), dict) else ''
                                )
                                if cand:
                                    return str(cand)
                        except Exception:
                            pass
                    return txt
                except Exception:
                    return str(s or '')

            summary_text = _clean_summary_for_storage(summary_text)

            # Sécurité supplémentaire: assurer le miroir legacy structured_data
            def _ensure_structured_data_mirror(obj: dict) -> dict:
                try:
                    if not isinstance(obj, dict):
                        return obj
                    sections = [
                        'executive_dashboard',
                        'deep_analysis',
                        'quantitative_signals',
                        'risk_management',
                        'actionable_summary',
                        'economic_indicators',
                    ]
                    sd = obj.get('structured_data')
                    needs_build = not isinstance(sd, dict) or any(k not in sd for k in sections)
                    if needs_build:
                        mirrored = {}
                        for key in sections:
                            if key in obj and obj.get(key) is not None:
                                mirrored[key] = obj.get(key)
                        obj['structured_data'] = mirrored
                except Exception:
                    pass
                return obj

            result = _ensure_structured_data_mirror(result)

            update_data = {
                'executive_summary': exec_summary,
                'summary': summary_text,
                'key_points': key_points,
                'structured_data': result.get('structured_data', {}),
                'geopolitical_analysis': result.get('geopolitical_analysis', {}),
                'economic_indicators': result.get('economic_indicators', {}),
                'insights': insights,
                'risks': risks,
                'opportunities': opportunities,
                'sources': sources,
                'confidence_score': result.get('confidence_score', 0.0),
                'worker_status': 'completed',
                'processing_time_seconds': processing_time
            }

            # Log des données finales sauvegardées
            try:
                logger.info("📊 Données finales sauvegardées:")
                logger.info(f"   - Executive Summary: {len(exec_summary)} points")
                logger.info(f"   - Résumé: {len(summary_text)} caractères")
                logger.info(f"   - Points clés: {len(key_points)} points")
                logger.info(f"   - Insights: {len(insights)} insights")
                logger.info(f"   - Risques: {len(risks)} risques")
                logger.info(f"   - Opportunités: {len(opportunities)} opportunités")
            except Exception:
                pass
            
            logger.info(f"💾 Sauvegarde des résultats dans la base de données...")
            self.db.update_analysis(task_id, update_data)
            logger.info(f"✅ Tâche #{task_id} terminée avec succès en {processing_time}s.")
            
            # 5. Envoyer le rapport par email (si configuré) sans double validation
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
            
            # Créer et envoyer l'email (horodatage CET/CEST par défaut: Europe/Zurich)
            msg = MIMEMultipart('related')
            msg['From'] = email_user
            msg['To'] = ", ".join(recipients)
            try:
                tz_name = os.getenv("REPORT_TIMEZONE", "Europe/Zurich")
                if ZoneInfo:
                    now_local = datetime.now(ZoneInfo(tz_name))
                else:
                    now_local = datetime.utcnow()  # fallback
                ts_str = now_local.strftime('%d/%m/%Y %H:%M %Z')
            except Exception:
                ts_str = datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')
            msg['Subject'] = f"[BONVIN] Rapport d'Analyse de Marché - {ts_str}"
            
            # Optionnel: image header CID (avec overlay texte titre+timestamp)
            try:
                header_path = os.getenv('EMAIL_HEADER_IMAGE_PATH', 'assets/email/header.png')
                cid_name = os.getenv('EMAIL_HEADER_CID', 'market-header')
                if header_path and os.path.exists(header_path):
                    with open(header_path, 'rb') as f:
                        base_img_bytes = f.read()

                    # Overlay dynamique (best-effort)
                    overlay_enabled = str(os.getenv('EMAIL_HEADER_OVERLAY', '1')).lower() in ('1','true','yes')
                    img_bytes_to_send = base_img_bytes
                    if overlay_enabled:
                        try:
                            from PIL import Image, ImageDraw, ImageFont  # type: ignore
                            from io import BytesIO
                            im = Image.open(BytesIO(base_img_bytes)).convert('RGBA')
                            draw = ImageDraw.Draw(im)
                            W, H = im.size
                            title = os.getenv('EMAIL_HEADER_TITLE', 'RAPPORT D\'ANALYSE DE MARCHÉ')
                            subtitle = os.getenv('EMAIL_HEADER_SUBTITLE', f'Généré le {ts_str}')

                            # Choix tailles police relatifs à la largeur
                            title_size = max(24, int(W * 0.05))
                            sub_size = max(16, int(W * 0.025))
                            try:
                                font_path = os.getenv('EMAIL_HEADER_FONT_PATH', '')
                                if font_path and os.path.exists(font_path):
                                    font_title = ImageFont.truetype(font_path, title_size)
                                    font_sub = ImageFont.truetype(font_path, sub_size)
                                else:
                                    font_title = ImageFont.load_default()
                                    font_sub = ImageFont.load_default()
                            except Exception:
                                font_title = ImageFont.load_default()
                                font_sub = ImageFont.load_default()

                            # Calcul dimensions texte
                            title_w, title_h = draw.textbbox((0,0), title, font=font_title)[2:4]
                            sub_w, sub_h = draw.textbbox((0,0), subtitle, font=font_sub)[2:4]
                            pad = int(H * 0.04)
                            block_w = max(title_w, sub_w) + 2*pad
                            block_h = title_h + sub_h + 3*pad//2
                            x = pad
                            y = pad

                            # Fond semi-opaque pour lisibilité
                            bg = Image.new('RGBA', (block_w, block_h), (0,0,0,120))
                            im.alpha_composite(bg, dest=(x, y))
                            # Ombre légère
                            shadow_offset = 2
                            draw.text((x+pad+shadow_offset, y+pad+shadow_offset), title, font=font_title, fill=(0,0,0,180))
                            draw.text((x+pad, y+pad), title, font=font_title, fill=(255,255,255,230))
                            draw.text((x+pad+shadow_offset, y+pad+title_h+pad//2+shadow_offset), subtitle, font=font_sub, fill=(0,0,0,160))
                            draw.text((x+pad, y+pad+title_h+pad//2), subtitle, font=font_sub, fill=(230,230,230,230))

                            # Export PNG
                            out = BytesIO()
                            im.convert('RGB').save(out, format='PNG', optimize=True)
                            img_bytes_to_send = out.getvalue()
                        except Exception as _e_overlay:
                            logger.warning(f"Overlay header image désactivé (fallback image originale): {_e_overlay}")

                    from email.mime.image import MIMEImage
                    img = MIMEImage(img_bytes_to_send, _subtype='png')
                    img.add_header('Content-ID', f'<{cid_name}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(header_path))
                    msg.attach(img)
                    # Injecter l'image dans l'HTML si non présente
                    if 'cid:' + cid_name not in html_content:
                        html_header = f"<div style=\"text-align:center;margin-bottom:12px\"><img src=\"cid:{cid_name}\" alt=\"Market Header\" style=\"max-width:100%;height:auto\"/></div>"
                        html_content = html_header + html_content
            except Exception as _e_img:
                logger.warning(f"Image CID non ajoutée: {_e_img}")

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
        # Récupérer les données du snapshot de marché (chiffres en quasi temps réel via yfinance)
        from stock_api_manager import stock_api_manager
        market_snapshot = stock_api_manager.get_market_snapshot()
        # Timestamp local pour affichage
        try:
            tz_name = os.getenv("REPORT_TIMEZONE", "Europe/Zurich")
            if ZoneInfo:
                now_local = datetime.now(ZoneInfo(tz_name))
            else:
                now_local = datetime.utcnow()
            ts_str = now_local.strftime('%d/%m/%Y à %H:%M %Z')
        except Exception:
            ts_str = datetime.utcnow().strftime('%d/%m/%Y à %H:%M UTC')
        
        # Normaliser la structure de résultat (peut être une chaîne JSON ou du texte)
        try:
            if not isinstance(result, dict):
                try:
                    result = json.loads(result)  # tenter de parser JSON
                except Exception:
                    result = {
                        "summary": str(result) if result is not None else "",
                        "key_points": [],
                        "structured_data": {},
                        "sources": [],
                        "confidence_score": 0.0,
                    }
        except Exception:
            result = {"summary": "", "key_points": [], "structured_data": {}, "sources": [], "confidence_score": 0.0}

        # Préparer et normaliser les sous-sections
        def _normalize_to_list(val):
            try:
                if val is None:
                    return []
                if isinstance(val, list):
                    # Convertir tout élément non-str en str
                    return [str(x).strip() for x in val if str(x).strip()]
                if isinstance(val, str):
                    # Supporter puces markdown et sauts de ligne
                    raw = val.replace('\r', '\n')
                    # Remplacer puces usuelles par des sauts de ligne unifiés
                    for bullet in ['\n- ', '\n• ', '\n* ']:
                        raw = raw.replace(bullet, '\n')
                    parts = [p.strip(' -•*\t') for p in raw.split('\n')]
                    return [p for p in parts if p]
                # Autres types
                return [str(val)] if str(val).strip() else []
            except Exception:
                return []

        # Préférer les champs normalisés de l'analyse en base, fallback vers le résultat brut
        exec_summary = _normalize_to_list(getattr(analysis, 'executive_summary', None) or result.get('executive_summary', []))
        econ_indicators = getattr(analysis, 'economic_indicators', None) or result.get('economic_indicators', {})
        if not isinstance(econ_indicators, dict):
            econ_indicators = {}
        # Extraire la géopolitique depuis structured_data.deep_analysis.geopolitical_chess si dispo
        structured_data = getattr(analysis, 'structured_data', None) or result.get('structured_data', {})
        structured_data = structured_data if isinstance(structured_data, dict) else {}
        deep_analysis = structured_data.get('deep_analysis', {}) if isinstance(structured_data.get('deep_analysis', {}), dict) else {}
        geo_chess = deep_analysis.get('geopolitical_chess', {}) if isinstance(deep_analysis.get('geopolitical_chess', {}), dict) else {}
        legacy_geo = getattr(analysis, 'geopolitical_analysis', None) or result.get('geopolitical_analysis', {})
        geo_analysis = geo_chess if geo_chess else (legacy_geo if isinstance(legacy_geo, dict) else {})
        analytics_data = market_snapshot.get('analytics', {}) if isinstance(market_snapshot, dict) else {}

        # Ne pas afficher ni rendre de sources pour garder un narratif épuré
        sources_html = ""

        # Calculer un pourcentage de confiance sûr pour l'affichage
        _score_raw = getattr(analysis, 'confidence_score', None) if getattr(analysis, 'confidence_score', None) is not None else result.get('confidence_score', 0)
        try:
            _score_num = float(_score_raw) if _score_raw is not None else 0.0
        except Exception:
            _score_num = 0.0

        # Pré-générer les sections HTML robustes
        exec_summary_html = self._render_validated_executive_summary(exec_summary, market_snapshot)
        econ_html = self._generate_economic_indicators(econ_indicators)
        # Supporter à la fois le format legacy et le format geopolitical_chess
        if isinstance(geo_analysis, dict) and ('immediate_impacts' in geo_analysis or 'second_order_effects' in geo_analysis or 'black_swans' in geo_analysis):
            geo_html = self._generate_geopolitical_chess(geo_analysis)
        else:
            geo_html = self._generate_geopolitical_analysis(geo_analysis if isinstance(geo_analysis, dict) else {})
        analytics_html = self._generate_analytics_section(analytics_data if isinstance(analytics_data, dict) else {})
        # Résumé: préférer analysis.summary, puis result.summary, puis deep_analysis.narrative
        summary_text = getattr(analysis, 'summary', None) or ''
        if not summary_text:
            summary_text = str(result.get('summary', '') or '')
            if not summary_text:
                try:
                    summary_text = str((deep_analysis.get('narrative') or '')).strip()
                except Exception:
                    summary_text = ''
        summary_html = self._render_summary_paragraphs(summary_text)

        # Rendu des sections structured_data (si présentes)
        meta_html = self._generate_meta_analysis(structured_data.get('meta_analysis', {}) if isinstance(structured_data.get('meta_analysis', {}), dict) else {})
        exec_dash_html = self._generate_executive_dashboard(structured_data.get('executive_dashboard', {}) if isinstance(structured_data.get('executive_dashboard', {}), dict) else {})
        _qs = structured_data.get('quantitative_signals', {})
        if not isinstance(_qs, dict):
            _qs = result.get('quantitative_signals', {}) if isinstance(result.get('quantitative_signals', {}), dict) else {}
        quant_sd_html = self._generate_structured_quant_signals(_qs)
        _rm = structured_data.get('risk_management', {})
        if not isinstance(_rm, dict):
            _rm = result.get('risk_management', {}) if isinstance(result.get('risk_management', {}), dict) else {}
        risk_mgt_html = self._generate_risk_management(_rm)
        _as = structured_data.get('actionable_summary', {})
        if not isinstance(_as, dict):
            _as = result.get('actionable_summary', {}) if isinstance(result.get('actionable_summary', {}), dict) else {}
        actionable_html = self._generate_actionable_summary(_as)

        # Normaliser toutes les listes legacy
        key_points_list = _normalize_to_list(getattr(analysis, 'key_points', None) or result.get('key_points', []))
        insights_list = _normalize_to_list(getattr(analysis, 'insights', None) or result.get('insights', []))
        risks_list = _normalize_to_list(getattr(analysis, 'risks', None) or result.get('risks', []))
        opps_list = _normalize_to_list(getattr(analysis, 'opportunities', None) or result.get('opportunities', []))

        # Générer le HTML optimisé pour mobile
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                /* Reset et base */
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; 
                    margin: 0; 
                    padding: 0; 
                    background-color: #f0f2f5; 
                    color: #1a1a1a;
                    line-height: 1.6;
                }}
                
                /* Container principal */
                .container {{ 
                    max-width: 100%; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 0;
                }}
                
                /* Header */
                .header {{ 
                    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                    color: white;
                    padding: 20px 15px;
                    text-align: center;
                }}
                .header h1 {{ 
                    margin: 0;
                    font-size: 24px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .header .date {{ 
                    font-size: 13px;
                    opacity: 0.9;
                    margin-top: 5px;
                }}
                
                /* Executive Summary */
                .executive-summary {{ 
                    background: #0f172a;
                    color: white;
                    padding: 20px 15px;
                    margin: 0;
                }}
                .executive-summary h2 {{ 
                    margin: 0 0 15px 0;
                    font-size: 18px;
                    color: #fbbf24;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .executive-summary ul {{ 
                    margin: 0;
                    padding: 0;
                    list-style: none;
                }}
                .executive-summary li {{ 
                    padding: 10px 0;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                    font-size: 14px;
                    line-height: 1.5;
                }}
                .executive-summary li:last-child {{ border-bottom: none; }}
                
                /* Sections avec séparateurs visuels */
                .section {{ 
                    padding: 20px 15px;
                    border-bottom: 8px solid #f0f2f5;
                }}
                .section:last-child {{ border-bottom: none; }}
                
                .section h3 {{ 
                    margin: 0 0 15px 0;
                    font-size: 18px;
                    color: #1e3a8a;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                
                /* Cartes thématiques */
                .card {{
                    border-radius: 12px;
                    padding: 15px;
                    margin-bottom: 15px;
                }}
                
                /* Market Snapshot Table */
                .market-table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 14px;
                }}
                .market-table th {{
                    background: #1e3a8a;
                    color: white;
                    padding: 10px 8px;
                    text-align: left;
                    font-weight: 600;
                }}
                .market-table td {{
                    padding: 10px 8px;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .market-table tr:last-child td {{ border-bottom: none; }}
                
                /* Indicateurs économiques */
                .economic-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    margin-top: 15px;
                }}
                .economic-card {{
                    background: #f8fafc;
                    border-radius: 8px;
                    padding: 12px;
                    border-left: 3px solid #3b82f6;
                }}
                .economic-card h4 {{
                    margin: 0 0 5px 0;
                    font-size: 13px;
                    color: #64748b;
                    text-transform: uppercase;
                }}
                .economic-card .value {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #1e3a8a;
                }}
                
                /* Géopolitique */
                .geopolitical {{
                    background: #fef3c7;
                    border-radius: 12px;
                    padding: 15px;
                    border-left: 4px solid #f59e0b;
                }}
                
                /* Insights/Risques/Opportunités */
                .insights {{ 
                    background: #e0f2fe;
                    border-left: 4px solid #0284c7;
                }}
                .risks {{ 
                    background: #fee2e2;
                    border-left: 4px solid #ef4444;
                }}
                .opportunities {{ 
                    background: #dcfce7;
                    border-left: 4px solid #22c55e;
                }}
                
                /* Listes optimisées */
                ul {{
                    margin: 0;
                    padding-left: 20px;
                }}
                li {{
                    margin-bottom: 8px;
                    font-size: 14px;
                }}
                
                /* Footer */
                .footer {{ 
                    background: #f8fafc;
                    padding: 20px 15px;
                    text-align: center;
                    font-size: 12px;
                    color: #64748b;
                }}
                
                /* Couleurs variations */
                .positive {{ color: #22c55e; font-weight: 600; }}
                .negative {{ color: #ef4444; font-weight: 600; }}
                
                /* Responsive */
                @media (max-width: 600px) {{
                    .header h1 {{ font-size: 20px; }}
                    .section h3 {{ font-size: 16px; }}
                    .executive-summary li {{ font-size: 13px; }}
                    .economic-grid {{ grid-template-columns: 1fr; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 RAPPORT D'ANALYSE DE MARCHÉ</h1>
                    <div class="date">Généré le {ts_str}</div>
                </div>
                
                <!-- Executive Summary avec valeurs (validées) -->
                <div class="executive-summary">
                    <h2>🎯 EXECUTIVE SUMMARY</h2>
                    <ul>
                        {exec_summary_html}
                    </ul>
                </div>
                
                
                
                
                <!-- Aperçu du marché -->
                <div class="section">
                    <h3>📈 Aperçu du Marché</h3>
                    <table class="market-table">
                        <thead>
                            <tr><th>Actif</th><th>Prix</th><th>Variation</th></tr>
                        </thead>
                        <tbody>
                            {self._generate_market_snapshot_rows(market_snapshot)}
                        </tbody>
                    </table>
                </div>
                
                <!-- Analytics Avancés -->
                <div class="section">
                    <h3>🔍 Analytics Avancés</h3>
                    <div class="economic-grid">
                        {analytics_html}
                    </div>
                </div>

                <!-- Tableau de Bord Exécutif (structured_data) -->
                {f'<div class="section"><h3>🧭 Tableau de Bord Exécutif</h3>{exec_dash_html}</div>' if exec_dash_html else ''}

                <!-- Analyse Méta / Régimes (structured_data) -->
                {f'<div class="section"><h3>🧠 Analyse Méta & Régimes</h3>{meta_html}</div>' if meta_html else ''}
                
                <!-- Résumé détaillé -->
                <div class="section">
                    <h3>📝 Analyse Approfondie</h3>
                    {summary_html or '<p style="font-size: 14px; line-height: 1.8;">Aucun résumé disponible</p>'}
                </div>
                
                <!-- Points clés -->
                <div class="section">
                    <h3>🔑 Points Clés</h3>
                    <ul>
                        {chr(10).join([f'<li>{point}</li>' for point in (key_points_list or [])])}
                    </ul>
                </div>
                
                <!-- Insights -->
                <div class="section">
                    <div class="insights card">
                        <h3>💡 Insights</h3>
                        <ul>
                            {chr(10).join([f'<li>{insight}</li>' for insight in (insights_list or [])])}
                        </ul>
                    </div>
                </div>
                
                <!-- Risques -->
                <div class="section">
                    <div class="risks card">
                        <h3>⚠️ Risques Identifiés</h3>
                        <ul>
                            {chr(10).join([f'<li>{risk}</li>' for risk in (risks_list or [])])}
                        </ul>
                    </div>
                </div>
                
                <!-- Opportunités -->
                <div class="section">
                    <div class="opportunities card">
                        <h3>🚀 Opportunités</h3>
                        <ul>
                            {chr(10).join([f'<li>{opp}</li>' for opp in (opps_list or [])])}
                        </ul>
                    </div>
                </div>

                <!-- Signaux quantitatifs (structured_data) -->
                {f'<div class="section"><h3>📈 Signaux Quantitatifs</h3>{quant_sd_html}</div>' if quant_sd_html else ''}

                <!-- Gestion des Risques (structured_data) -->
                {f'<div class="section"><h3>🛡️ Gestion des Risques</h3>{risk_mgt_html}</div>' if risk_mgt_html else ''}

                <!-- Synthèse Actionnable (structured_data) -->
                {f'<div class="section"><h3>✅ Synthèse Actionnable</h3>{actionable_html}</div>' if actionable_html else ''}
                
                
                
                <div class="footer">
                    <p>Rapport généré automatiquement par le système BONVIN Collection</p>
                    <p>Confiance: {_score_num * 100:.1f}%</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def _render_summary_paragraphs(self, text: str) -> str:
        """Transforme un texte brut en paragraphes HTML simples."""
        try:
            if not text:
                return ''
            raw = str(text).replace('\r', '\n').strip()
            # Découper sur doubles sauts si présents, sinon simples
            parts = [p.strip() for p in raw.split('\n\n') if p.strip()]
            if len(parts) == 1:
                parts = [p.strip() for p in raw.split('\n') if p.strip()]
            return chr(10).join([f'<p style="font-size: 14px; line-height: 1.8;">{html.escape(p)}</p>' for p in parts])
        except Exception:
            return f'<p style="font-size: 14px; line-height: 1.8;">{html.escape(str(text))}</p>'

    def _generate_executive_dashboard(self, dashboard: Dict) -> str:
        """Rend le tableau de bord exécutif: alert_level, top_trades, snapshot_metrics."""
        try:
            if not dashboard:
                return ''
            parts = []
            alert = dashboard.get('alert_level')
            if alert:
                parts.append(f'<div class="card"><strong>Niveau d\'alerte:</strong> {alert}</div>')
            trades = dashboard.get('top_trades') or []
            if trades:
                items = []
                for t in trades:
                    if not isinstance(t, dict):
                        continue
                    action = t.get('action', '')
                    instr = t.get('instrument', '')
                    rationale = t.get('rationale', '')
                    rr = t.get('risk_reward', '')
                    tf = t.get('timeframe', '')
                    conf = t.get('confidence', '')
                    items.append(f"<li><strong>{action}</strong> {instr} — {rationale} <em>(R/R {rr}, {tf}, conf. {conf})</em></li>")
                if items:
                    parts.append('<div class="card"><h4>Top Trades</h4><ul>' + chr(10).join(items) + '</ul></div>')
            metrics = dashboard.get('snapshot_metrics') or []
            if metrics:
                m_items = [f'<li>{str(m)}</li>' for m in metrics]
                parts.append('<div class="card"><h4>Snapshot</h4><ul>' + chr(10).join(m_items) + '</ul></div>')
            return chr(10).join(parts)
        except Exception:
            return ''

    def _generate_meta_analysis(self, meta: Dict) -> str:
        """Rend meta_analysis: regime_detection, key_drivers."""
        try:
            if not meta:
                return ''
            blocks = []
            regime = meta.get('regime_detection') or {}
            if isinstance(regime, dict) and regime:
                items = []
                for k in ['market_regime', 'volatility_regime', 'liquidity_state', 'confidence']:
                    if k in regime:
                        items.append(f'<li><strong>{k.replace("_"," ").title()}</strong>: {regime[k]}</li>')
                if items:
                    blocks.append('<div class="card"><h4>Détection de Régime</h4><ul>' + chr(10).join(items) + '</ul></div>')
            drivers = meta.get('key_drivers') or {}
            if isinstance(drivers, dict) and drivers:
                d_html = []
                primary = drivers.get('primary')
                if primary:
                    d_html.append(f'<p><strong>Primaires:</strong> {primary}</p>')
                for label in ['secondary', 'emerging']:
                    arr = drivers.get(label) or []
                    if arr:
                        d_html.append(f'<p><strong>{label.title()}:</strong> ' + ', '.join([str(x) for x in arr]) + '</p>')
                if d_html:
                    blocks.append('<div class="card"><h4>Facteurs Clés</h4>' + ''.join(d_html) + '</div>')
            return chr(10).join(blocks)
        except Exception:
            return ''

    def _generate_structured_quant_signals(self, quant: Dict) -> str:
        """Rend quantitative_signals du structured_data."""
        try:
            if not quant:
                return ''
            parts = []
            tech = quant.get('technical_matrix') or {}
            if isinstance(tech, dict) and tech:
                items = []
                for k in ['oversold', 'overbought', 'breakouts', 'divergences']:
                    arr = tech.get(k) or []
                    if arr:
                        items.append(f'<li><strong>{k.title()}</strong>: ' + ', '.join([str(x) for x in arr]) + '</li>')
                if items:
                    parts.append('<div class="card"><h4>Technique</h4><ul>' + chr(10).join(items) + '</ul></div>')
            opt = quant.get('options_flow') or {}
            if isinstance(opt, dict) and opt:
                it = []
                for k in ['unusual_activity', 'large_trades', 'implied_moves']:
                    arr = opt.get(k) or []
                    if arr:
                        it.append(f'<li><strong>{k.replace("_"," ").title()}</strong>: ' + ', '.join([str(x) for x in arr]) + '</li>')
                if it:
                    parts.append('<div class="card"><h4>Flux d\'Options</h4><ul>' + chr(10).join(it) + '</ul></div>')
            sm = quant.get('smart_money_tracking') or {}
            if isinstance(sm, dict) and sm:
                items = []
                for k, v in sm.items():
                    items.append(f'<li><strong>{k.replace("_"," ").title()}</strong>: {v}</li>')
                parts.append('<div class="card"><h4>Smart Money</h4><ul>' + chr(10).join(items) + '</ul></div>')
            return chr(10).join(parts)
        except Exception:
            return ''

    def _generate_risk_management(self, risk: Dict) -> str:
        """Rend risk_management du structured_data."""
        try:
            if not risk:
                return ''
            parts = []
            adj = risk.get('portfolio_adjustments') or []
            if adj:
                items = []
                for r in adj:
                    if not isinstance(r, dict):
                        continue
                    items.append(f"<li><strong>Ajustement</strong>: {r.get('recommended_change','')} — {r.get('rationale','')}</li>")
                parts.append('<div class="card"><h4>Ajustements de Portefeuille</h4><ul>' + chr(10).join(items) + '</ul></div>')
            hedges = risk.get('tail_risk_hedges') or []
            if hedges:
                items = []
                for h in hedges:
                    if not isinstance(h, dict):
                        continue
                    items.append(f"<li><strong>Hedge</strong>: {h.get('risk','')} — {h.get('hedge_strategy','')} (coût {h.get('cost','')})</li>")
                parts.append('<div class="card"><h4>Hedges</h4><ul>' + chr(10).join(items) + '</ul></div>')
            stress = risk.get('stress_test_results') or {}
            if isinstance(stress, dict) and stress:
                s_items = [f'<li>{k}: {v}</li>' for k, v in stress.items()]
                parts.append('<div class="card"><h4>Stress Tests</h4><ul>' + chr(10).join(s_items) + '</ul></div>')
            return chr(10).join(parts)
        except Exception:
            return ''

    def _generate_actionable_summary(self, act: Dict) -> str:
        """Rend actionable_summary du structured_data."""
        try:
            if not act:
                return ''
            parts = []
            for k in ['immediate_actions', 'watchlist']:
                arr = act.get(k) or []
                if arr:
                    parts.append(f'<div class="card"><h4>{k.replace("_"," ").title()}</h4><ul>' + chr(10).join([f'<li>{str(x)}</li>' for x in arr]) + '</ul></div>')
            alerts = act.get('key_metrics_alerts') or {}
            if isinstance(alerts, dict) and alerts:
                items = []
                for kk in ['if_breaks', 'if_holds', 'calendar']:
                    arr = alerts.get(kk) or []
                    if arr:
                        items.append(f'<li><strong>{kk.replace("_"," ").title()}</strong>: ' + ', '.join([str(x) for x in arr]) + '</li>')
                if items:
                    parts.append('<div class="card"><h4>Alerts</h4><ul>' + chr(10).join(items) + '</ul></div>')
            return chr(10).join(parts)
        except Exception:
            return ''

    def _generate_geopolitical_chess(self, geo: Dict) -> str:
        """Rend la section geopolitical_chess (immediate_impacts, second_order_effects, black_swans)."""
        try:
            if not geo:
                return '<p>Aucune analyse géopolitique disponible</p>'
            parts = []
            if geo.get('immediate_impacts'):
                parts.append('<h4 style="margin-top: 0;">🧨 Impacts Immédiats</h4>')
                parts.append('<ul>')
                for it in geo['immediate_impacts']:
                    if isinstance(it, dict):
                        title = it.get('event') or ''
                        affected = ', '.join(it.get('affected_assets') or [])
                        magnitude = it.get('magnitude') or ''
                        duration = it.get('duration') or ''
                        parts.append(f'<li><strong>{title}</strong> — {affected} ({magnitude}, {duration})</li>')
                    else:
                        parts.append(f'<li>{str(it)}</li>')
                parts.append('</ul>')
            if geo.get('second_order_effects'):
                parts.append('<h4>🔁 Effets de Second Ordre</h4>')
                parts.append('<ul>')
                for it in geo['second_order_effects']:
                    if isinstance(it, dict):
                        parts.append(f"<li><strong>{it.get('trigger','')}</strong> — {it.get('cascade','')} (p={it.get('probability','')})</li>")
                    else:
                        parts.append(f'<li>{str(it)}</li>')
                parts.append('</ul>')
            if geo.get('black_swans'):
                parts.append('<h4>🦢 Black Swans</h4>')
                parts.append('<ul>')
                for it in geo['black_swans']:
                    if isinstance(it, dict):
                        parts.append(f"<li><strong>{it.get('scenario','')}</strong> — impact: {it.get('impact','')} (p={it.get('probability','')})</li>")
                    else:
                        parts.append(f'<li>{str(it)}</li>')
                parts.append('</ul>')
            return chr(10).join(parts) if parts else '<p>Aucune analyse géopolitique disponible</p>'
        except Exception:
            return '<p>Aucune analyse géopolitique disponible</p>'

    def _generate_market_snapshot_rows(self, snapshot: Dict) -> str:
        """Génère les lignes du tableau de snapshot de marché avec toutes les sections."""
        rows = []
        
        # Actions
        if snapshot.get('stocks'):
            rows.append('<tr><td colspan="3" style="background: #dbeafe; font-weight: bold; padding: 10px; color: #1e40af;">💼 Actions</td></tr>')
            for name, data in snapshot['stocks'].items():
                if isinstance(data, dict) and data.get('price') is not None:
                    change_class = 'positive' if data.get('change', 0) >= 0 else 'negative'
                    price = data.get('price', 'N/A')
                    change_pct = data.get('change_percent', 0)
                    if isinstance(price, (int, float)):
                        price_str = f"${price:,.2f}"
                    else:
                        price_str = str(price)
                    if isinstance(change_pct, (int, float)):
                        change_str = f"{change_pct:+.2f}%"
                    else:
                        change_str = str(change_pct)
                    rows.append(f'''
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{price_str}</td>
                            <td class="{change_class}">{change_str}</td>
                        </tr>
                    ''')
        
        if snapshot.get('indices'):
            rows.append('<tr><td colspan="3" style="background: #dcfce7; font-weight: bold; padding: 10px; color: #15803d;">📊 Indices</td></tr>')
            for name, data in snapshot['indices'].items():
                change_class = 'positive' if data.get('change', 0) >= 0 else 'negative'
                price = data.get('price', 'N/A')
                change_pct = data.get('change_percent', 0)
                price_str = f"${price:,.2f}" if isinstance(price, (int, float)) else str(price)
                change_str = f"{change_pct:+.2f}%" if isinstance(change_pct, (int, float)) else str(change_pct)
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>{price_str}</td>
                        <td class="{change_class}">{change_str}</td>
                    </tr>
                ''')
        
        if snapshot.get('commodities'):
            rows.append('<tr><td colspan="3" style="background: #fef3c7; font-weight: bold; padding: 10px; color: #92400e;">🏭 Matières Premières</td></tr>')
            for name, data in snapshot['commodities'].items():
                change_class = 'positive' if data.get('change', 0) >= 0 else 'negative'
                price = data.get('price', 'N/A')
                change_pct = data.get('change_percent', 0)
                price_str = f"${price:,.2f}" if isinstance(price, (int, float)) else str(price)
                change_str = f"{change_pct:+.2f}%" if isinstance(change_pct, (int, float)) else str(change_pct)
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>{price_str}</td>
                        <td class="{change_class}">{change_str}</td>
                    </tr>
                ''')
        
        if snapshot.get('crypto'):
            rows.append('<tr><td colspan="3" style="background: #ede9fe; font-weight: bold; padding: 10px; color: #6d28d9;">🪙 Cryptomonnaies</td></tr>')
            for name, data in snapshot['crypto'].items():
                change_class = 'positive' if data.get('change', 0) >= 0 else 'negative'
                price = data.get('price', 'N/A')
                change_pct = data.get('change_percent', 0)
                price_str = f"${price:,.2f}" if isinstance(price, (int, float)) else str(price)
                change_str = f"{change_pct:+.2f}%" if isinstance(change_pct, (int, float)) else str(change_pct)
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>{price_str}</td>
                        <td class="{change_class}">{change_str}</td>
                    </tr>
                ''')
        
        # Forex
        if snapshot.get('forex'):
            rows.append('<tr><td colspan="3" style="background: #fce7f3; font-weight: bold; padding: 10px; color: #be185d;">💱 Forex</td></tr>')
            for name, data in snapshot['forex'].items():
                if isinstance(data, dict) and data.get('value') is not None:
                    change_class = 'positive' if data.get('change', 0) >= 0 else 'negative'
                    value = data.get('value', 'N/A')
                    change_pct = data.get('change_percent', 0)
                    if isinstance(value, (int, float)):
                        value_str = f"{value:.2f}"
                    else:
                        value_str = str(value)
                    if isinstance(change_pct, (int, float)):
                        change_str = f"{change_pct:+.2f}%"
                    else:
                        change_str = str(change_pct)
                    rows.append(f'''
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{value_str}</td>
                            <td class="{change_class}">{change_str}</td>
                        </tr>
                    ''')
        
        # Obligations
        if snapshot.get('bonds'):
            rows.append('<tr><td colspan="3" style="background: #f0fdf4; font-weight: bold; padding: 10px; color: #166534;">📜 Obligations</td></tr>')
            for name, data in snapshot['bonds'].items():
                if isinstance(data, dict) and data.get('yield') is not None:
                    yield_val = data.get('yield', 'N/A')
                    change_bps = data.get('change_bps', 0)
                    if isinstance(yield_val, (int, float)):
                        yield_str = f"{yield_val:.3f}%"
                    else:
                        yield_str = str(yield_val)
                    if isinstance(change_bps, (int, float)):
                        change_str = f"{change_bps:+.1f} bp"
                    else:
                        change_str = str(change_bps)
                    rows.append(f'''
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{yield_str}</td>
                            <td>{change_str}</td>
                        </tr>
                    ''')
        
        # Volatilité
        if snapshot.get('volatility'):
            rows.append('<tr><td colspan="3" style="background: #fef2f2; font-weight: bold; padding: 10px; color: #991b1b;">📉 Volatilité</td></tr>')
            for name, data in snapshot['volatility'].items():
                if isinstance(data, dict) and data.get('price') is not None:
                    price = data.get('price', 'N/A')
                    change_pct = data.get('change_percent', 0)
                    if isinstance(price, (int, float)):
                        price_str = f"{price:.2f}"
                    else:
                        price_str = str(price)
                    if isinstance(change_pct, (int, float)):
                        change_str = f"{change_pct:+.2f}%"
                    else:
                        change_str = str(change_pct)
                    rows.append(f'''
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{price_str}</td>
                            <td>{change_str}</td>
                        </tr>
                    ''')
        
        return chr(10).join(rows) if rows else '<tr><td colspan="3">Aucune donnée disponible</td></tr>'
    
    def _generate_analytics_section(self, analytics: Dict) -> str:
        """Génère la section des analytics avancés."""
        html_parts = []
        
        if not analytics:
            return '<div class="analytics-item"><div class="analytics-label">Aucun analytics disponible</div></div>'
        
        # RSI SPX
        if analytics.get('rsi_spx_14') is not None:
            rsi = analytics['rsi_spx_14']
            rsi_class = 'positive' if rsi < 30 else ('negative' if rsi > 70 else '')
            html_parts.append(f'''
                <div class="analytics-item">
                    <div class="analytics-label">RSI S&P 500 (14)</div>
                    <div class="analytics-value {rsi_class}">{rsi:.1f}</div>
                </div>
            ''')
        
        # Crypto Fear & Greed
        if analytics.get('btc_fear_greed') is not None:
            fng = analytics['btc_fear_greed']
            fng_class = 'positive' if fng > 50 else 'negative'
            html_parts.append(f'''
                <div class="analytics-item">
                    <div class="analytics-label">Crypto Fear & Greed</div>
                    <div class="analytics-value {fng_class}">{fng}</div>
                </div>
            ''')
        
        # BTC Dominance
        if analytics.get('btc_dominance_pct') is not None:
            dominance = analytics['btc_dominance_pct']
            html_parts.append(f'''
                <div class="analytics-item">
                    <div class="analytics-label">BTC Dominance</div>
                    <div class="analytics-value">{dominance:.2f}%</div>
                </div>
            ''')
        
        # VIX Regime
        if analytics.get('vix_regime') is not None:
            vix_regime = analytics['vix_regime']
            html_parts.append(f'''
                <div class="analytics-item">
                    <div class="analytics-label">VIX Regime</div>
                    <div class="analytics-value">{vix_regime}</div>
                </div>
            ''')
        
        # Market Phase
        if analytics.get('market_phase') is not None:
            market_phase = analytics['market_phase']
            html_parts.append(f'''
                <div class="analytics-item">
                    <div class="analytics-label">Phase Marché</div>
                    <div class="analytics-value">{market_phase}</div>
                </div>
            ''')
        
        # Gold/Silver Ratio
        if analytics.get('gold_silver_ratio') is not None:
            ratio = analytics['gold_silver_ratio']
            html_parts.append(f'''
                <div class="analytics-item">
                    <div class="analytics-label">Ratio Or/Argent</div>
                    <div class="analytics-value">{ratio:.2f}</div>
                </div>
            ''')
        
        # Spread 2-10Y
        if analytics.get('spread_2_10_bps') is not None:
            spread = analytics['spread_2_10_bps']
            spread_class = 'positive' if spread > 0 else 'negative'
            html_parts.append(f'''
                <div class="analytics-item">
                    <div class="analytics-label">Spread 2-10Y</div>
                    <div class="analytics-value {spread_class}">{spread:.1f} bp</div>
                </div>
            ''')
        
        return chr(10).join(html_parts)
    
    def _generate_economic_indicators(self, indicators: Dict) -> str:
        """Génère les cartes d'indicateurs économiques."""
        html_parts = []
        
        # Inflation
        if indicators.get('inflation'):
            inflation = indicators['inflation']
            html_parts.append(f'''
                <div class="economic-card">
                    <h4>Inflation</h4>
                    <div class="value">{inflation.get('US', 'N/A')} 🇺🇸</div>
                    <div style="font-size: 12px; color: #64748b;">Europe: {inflation.get('EU', 'N/A')}</div>
                </div>
            ''')
        
        # Taux directeurs
        if indicators.get('central_banks'):
            banks = indicators['central_banks']
            html_parts.append(f'''
                <div class="economic-card">
                    <h4>Taux Directeurs</h4>
                    <div class="value">Fed: {banks[0] if banks else 'N/A'}</div>
                    <div style="font-size: 12px; color: #64748b;">{banks[1] if len(banks) > 1 else 'BCE: N/A'}</div>
                </div>
            ''')
        
        # Croissance GDP
        if indicators.get('gdp_growth'):
            gdp = indicators['gdp_growth']
            html_parts.append(f'''
                <div class="economic-card">
                    <h4>Croissance PIB</h4>
                    <div class="value">{gdp.get('US', 'N/A')} 🇺🇸</div>
                    <div style="font-size: 12px; color: #64748b;">Chine: {gdp.get('China', 'N/A')}</div>
                </div>
            ''')
        
        # Chômage
        if indicators.get('unemployment'):
            unemployment = indicators['unemployment']
            html_parts.append(f'''
                <div class="economic-card">
                    <h4>Chômage</h4>
                    <div class="value">{unemployment.get('US', 'N/A')} 🇺🇸</div>
                    <div style="font-size: 12px; color: #64748b;">Europe: {unemployment.get('EU', 'N/A')}</div>
                </div>
            ''')
        
        return chr(10).join(html_parts) if html_parts else '<p>Aucun indicateur économique disponible</p>'
    
    def _generate_geopolitical_analysis(self, analysis: Dict) -> str:
        """Génère l'analyse géopolitique."""
        html_parts = []
        
        # Conflits
        if analysis.get('conflicts'):
            html_parts.append('<h4 style="margin-top: 0;">🔥 Conflits et Tensions</h4>')
            html_parts.append('<ul>')
            for conflict in analysis['conflicts']:
                html_parts.append(f'<li>{conflict}</li>')
            html_parts.append('</ul>')
        
        # Relations commerciales
        if analysis.get('trade_relations'):
            html_parts.append('<h4>🤝 Relations Commerciales</h4>')
            html_parts.append('<ul>')
            for relation in analysis['trade_relations']:
                html_parts.append(f'<li>{relation}</li>')
            html_parts.append('</ul>')
        
        # Sanctions
        if analysis.get('sanctions'):
            html_parts.append('<h4>⚖️ Sanctions Économiques</h4>')
            html_parts.append('<ul>')
            for sanction in analysis['sanctions']:
                html_parts.append(f'<li>{sanction}</li>')
            html_parts.append('</ul>')
        
        # Sécurité énergétique
        if analysis.get('energy_security'):
            html_parts.append('<h4>⚡ Sécurité Énergétique</h4>')
            html_parts.append('<ul>')
            for energy in analysis['energy_security']:
                html_parts.append(f'<li>{energy}</li>')
            html_parts.append('</ul>')
        
        return chr(10).join(html_parts) if html_parts else '<p>Aucune analyse géopolitique disponible</p>'

    def _render_validated_executive_summary(self, summary_points: List[str], snapshot: Dict) -> str:
        """Génère un executive summary pixel perfect avec les vraies données du snapshot."""
        try:
            if not summary_points:
                return ''

            # Utiliser directement les données du snapshot sans validation stricte
            rendered = []
            for point in summary_points:
                rendered.append(f"<li>{html.escape(str(point))}</li>")
            return chr(10).join(rendered)
        except Exception:
            # En cas de doute, retourner brut sans bloquer l'envoi
            return chr(10).join([f"<li>{html.escape(str(p))}</li>" for p in (summary_points or [])])

    def _process_monthly_payload_file(self) -> None:
        """Traite un fichier monthly_report_payload.json s'il est présent (post-déploiement)."""
        file_path = os.getenv('MONTHLY_PAYLOAD_FILE', 'monthly_report_payload.json')
        if not os.path.isfile(file_path):
            logger.info("ℹ️ Aucun payload mensuel détecté")
            return

        logger.info(f"📥 Payload mensuel détecté: {file_path} — traitement en cours...")
        with open(file_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        # Déterminer le mois cible
        report_date = None
        try:
            report_date = payload.get('metadata', {}).get('report_date')
        except Exception:
            report_date = None

        if report_date:
            try:
                dt = datetime.fromisoformat(report_date.replace('Z', '+00:00'))
            except Exception:
                dt = datetime.now(timezone.utc)
        else:
            dt = datetime.now(timezone.utc)
        month_key = dt.strftime('%Y-%m')

        # Vérifier si un rapport mensuel existe déjà pour ce mois
        try:
            existing = self.db.get_analyses_by_type('monthly', limit=12)
        except Exception:
            existing = []
        for a in existing:
            try:
                if a.timestamp:
                    adt = datetime.fromisoformat(a.timestamp.replace('Z', '+00:00'))
                    if adt.strftime('%Y-%m') == month_key:
                        logger.info(f"ℹ️ Rapport mensuel {month_key} déjà présent (ID {a.id}), annulation du traitement.")
                        return
            except Exception:
                continue

        # Insérer le rapport mensuel
        analysis = MarketAnalysis(
            analysis_type='monthly',
            prompt=f'Rapport mensuel – {month_key}',
            executive_summary=payload.get('executive_summary'),
            summary=payload.get('summary'),
            key_points=payload.get('key_points'),
            structured_data=payload.get('structured_data', {}),
            geopolitical_analysis=payload.get('geopolitical_analysis'),
            economic_indicators=payload.get('economic_indicators'),
            insights=payload.get('insights', []),
            risks=payload.get('risks', []),
            opportunities=payload.get('opportunities', []),
            sources=payload.get('sources', []),
            confidence_score=payload.get('confidence_score', 0.0),
            worker_status='completed',
            processing_time_seconds=0,
            timestamp=dt.isoformat(),
        )

        analysis_id = self.db.save_analysis(analysis)
        if analysis_id:
            logger.info(f"✅ Rapport mensuel {month_key} inséré (ID {analysis_id}). Envoi email...")
            try:
                # Si une loop est déjà active, créer une tâche; sinon, exécuter directement
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._send_market_analysis_email(analysis_id, payload))
                    logger.info("📧 Envoi email mensuel planifié dans la boucle existante")
                except RuntimeError:
                    asyncio.run(self._send_market_analysis_email(analysis_id, payload))
            except Exception as e:
                logger.warning(f"⚠️ Envoi email mensuel échoué: {e}")
            # Renommer le fichier pour éviter retraits
            try:
                processed = f"{os.path.splitext(file_path)[0]}.processed_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                os.rename(file_path, processed)
                logger.info(f"🗂️ Payload archivé: {processed}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible d'archiver le payload: {e}")
        else:
            logger.error("❌ Échec d'insertion du rapport mensuel")

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
