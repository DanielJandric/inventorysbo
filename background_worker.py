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
from typing import Dict, List
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
                'geopolitical_analysis': result.get('geopolitical_analysis', {}),
                'economic_indicators': result.get('economic_indicators', {}),
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
                    <div class="date">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</div>
                </div>
                
                <!-- Executive Summary avec valeurs (validées) -->
                <div class="executive-summary">
                    <h2>🎯 EXECUTIVE SUMMARY</h2>
                    <ul>
                        {self._render_validated_executive_summary(result.get('executive_summary', []), market_snapshot)}
                    </ul>
                </div>
                
                <!-- Indicateurs Économiques -->
                <div class="section">
                    <h3>📊 Indicateurs Économiques</h3>
                    <div class="economic-grid">
                        {self._generate_economic_indicators(result.get('economic_indicators', {}))}
                    </div>
                </div>
                
                <!-- Analyse Géopolitique -->
                <div class="section">
                    <h3>🌍 Analyse Géopolitique</h3>
                    <div class="geopolitical card">
                        {self._generate_geopolitical_analysis(result.get('geopolitical_analysis', {}))}
                    </div>
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
                
                <!-- Résumé détaillé -->
                <div class="section">
                    <h3>📝 Analyse Approfondie</h3>
                    <p style="font-size: 14px; line-height: 1.8;">{result.get('summary', 'Aucun résumé disponible')}</p>
                </div>
                
                <!-- Points clés -->
                <div class="section">
                    <h3>🔑 Points Clés</h3>
                    <ul>
                        {chr(10).join([f'<li>{point}</li>' for point in (result.get('key_points', []) or [])])}
                    </ul>
                </div>
                
                <!-- Insights -->
                <div class="section">
                    <div class="insights card">
                        <h3>💡 Insights</h3>
                        <ul>
                            {chr(10).join([f'<li>{insight}</li>' for insight in (result.get('insights', []) or [])])}
                        </ul>
                    </div>
                </div>
                
                <!-- Risques -->
                <div class="section">
                    <div class="risks card">
                        <h3>⚠️ Risques Identifiés</h3>
                        <ul>
                            {chr(10).join([f'<li>{risk}</li>' for risk in (result.get('risks', []) or [])])}
                        </ul>
                    </div>
                </div>
                
                <!-- Opportunités -->
                <div class="section">
                    <div class="opportunities card">
                        <h3>🚀 Opportunités</h3>
                        <ul>
                            {chr(10).join([f'<li>{opp}</li>' for opp in (result.get('opportunities', []) or [])])}
                        </ul>
                    </div>
                </div>
                
                <!-- Sources -->
                <div class="section">
                    <h3>📚 Sources d'Information</h3>
                    <ul style="list-style: none; padding: 0;">
                        {chr(10).join([f'<li style="margin-bottom: 8px;">📎 <a href="{source.get("url", "#")}" target="_blank" style="color: #3b82f6; text-decoration: none;">{source.get("title", "Source")}</a></li>' for source in (result.get('sources', []) or [])])}
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
            rows.append('<tr><td colspan="3" style="background: #e5e7eb; font-weight: bold; padding: 10px;">📊 Indices</td></tr>')
            for name, data in snapshot['indices'].items():
                change_class = 'positive' if data.get('change', 0) >= 0 else 'negative'
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>${data.get('price', 'N/A'):,.2f}</td>
                        <td class="{change_class}">{data.get('change_percent', 0):+.2f}%</td>
                    </tr>
                ''')
        
        if snapshot.get('commodities'):
            rows.append('<tr><td colspan="3" style="background: #e5e7eb; font-weight: bold; padding: 10px;">🏭 Matières Premières</td></tr>')
            for name, data in snapshot['commodities'].items():
                change_class = 'positive' if data.get('change', 0) >= 0 else 'negative'
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>${data.get('price', 'N/A'):,.2f}</td>
                        <td class="{change_class}">{data.get('change_percent', 0):+.2f}%</td>
                    </tr>
                ''')
        
        if snapshot.get('crypto'):
            rows.append('<tr><td colspan="3" style="background: #e5e7eb; font-weight: bold; padding: 10px;">🪙 Cryptomonnaies</td></tr>')
            for name, data in snapshot['crypto'].items():
                change_class = 'positive' if data.get('change', 0) >= 0 else 'negative'
                rows.append(f'''
                    <tr>
                        <td><strong>{name}</strong></td>
                        <td>${data.get('price', 'N/A'):,.2f}</td>
                        <td class="{change_class}">{data.get('change_percent', 0):+.2f}%</td>
                    </tr>
                ''')
        
        return chr(10).join(rows) if rows else '<tr><td colspan="3">Aucune donnée disponible</td></tr>'
    
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
        """Valide et rend les points de l'executive summary en interdisant toute invention de chiffres.

        Règle: si un point contient un actif dont la valeur n'est pas dans le snapshot, remplacer les parties chiffrées par 'N/A'.
        """
        try:
            if not summary_points:
                return ''

            # Construire une map de valeurs disponibles par nom logique simplifié
            def get_known_value(name: str) -> Optional[Dict]:
                name_l = name.lower()
                # Indices
                for k, v in (snapshot.get('indices') or {}).items():
                    if k.lower() in name_l:
                        return v
                # Volatility (VIX)
                for k, v in (snapshot.get('volatility') or {}).items():
                    if k.lower() in name_l:
                        return v
                # Commodities
                for k, v in (snapshot.get('commodities') or {}).items():
                    if k.lower() in name_l or name_l in k.lower():
                        return v
                # Crypto
                for k, v in (snapshot.get('crypto') or {}).items():
                    if k.lower() in name_l:
                        return v
                # Stocks
                for k, v in (snapshot.get('stocks') or {}).items():
                    if k.lower() in name_l:
                        return v
                return None

            rendered = []
            import re
            num_pattern = re.compile(r"\$?\d+[\d,\.]*%?|")

            for point in summary_points:
                checked_point = point
                # Déterminer un actif probable par mots-clés connus
                possible_keys = ['s&p', 'nasdaq', 'dow', 'vix', 'or', 'gold', 'bitcoin', 'btc', 'nvda', 'nvidia', 'msft', 'microsoft', 'amd', 'aapl', 'apple']
                matched_key = next((k for k in possible_keys if k in point.lower()), None)
                val = get_known_value(matched_key) if matched_key else None
                if not val or not isinstance(val, dict) or val.get('price') is None:
                    # Remplacer toute occurrence numérique par N/A
                    checked_point = re.sub(r"\$?\d+[\d,\.]*%?", "N/A", checked_point)
                rendered.append(f"<li>{checked_point}</li>")
            return chr(10).join(rendered)
        except Exception:
            # En cas de doute, retourner brut sans bloquer l'envoi
            return chr(10).join([f"<li>{p}</li>" for p in (summary_points or [])])

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
