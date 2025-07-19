import os
import json
import logging
import re
import hashlib
import smtplib
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from functools import lru_cache, wraps
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import configuration seulement si les variables ne sont pas déjà définies
if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
    try:
        import config
        print("✅ Configuration locale importée")
    except ImportError:
        print("⚠️ Fichier config.py non trouvé")
else:
    print("✅ Variables d'environnement déjà définies (déploiement)")

# Configuration logging sophistiquée
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache pour les prix des actions avec expiration
stock_price_cache = {}
STOCK_PRICE_CACHE_DURATION = 300  # 5 minutes (pour des mises à jour plus fréquentes)



# Cache pour les taux de change avec expiration
forex_cache = {}
FOREX_CACHE_DURATION = 3600  # 1 heure

# Classes de données sophistiquées
@dataclass
class CollectionItem:
    """Modèle de données enrichi pour un objet de collection"""
    name: str
    category: str
    status: str
    id: Optional[int] = None
    construction_year: Optional[int] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    asking_price: Optional[float] = None
    sold_price: Optional[float] = None
    acquisition_price: Optional[float] = None
    for_sale: bool = False
    sale_status: Optional[str] = None
    sale_progress: Optional[str] = None
    buyer_contact: Optional[str] = None
    intermediary: Optional[str] = None
    current_offer: Optional[float] = None
    commission_rate: Optional[float] = None
    last_action_date: Optional[str] = None
    surface_m2: Optional[float] = None
    rental_income_chf: Optional[float] = None
    # Champs spécifiques aux actions
    stock_symbol: Optional[str] = None
    stock_quantity: Optional[int] = None
    stock_purchase_price: Optional[float] = None
    stock_exchange: Optional[str] = None
    current_price: Optional[float] = None
    last_price_update: Optional[str] = None
    # Métriques boursières supplémentaires
    stock_volume: Optional[int] = None
    stock_pe_ratio: Optional[float] = None
    stock_52_week_high: Optional[float] = None
    stock_52_week_low: Optional[float] = None
    stock_change: Optional[float] = None
    stock_change_percent: Optional[float] = None
    stock_average_volume: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionItem':
        """Crée une instance depuis un dictionnaire"""
        # Filtrer seulement les champs valides
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)

class QueryIntent(Enum):
    """Types d'intentions sophistiquées"""
    VEHICLE_ANALYSIS = "vehicle_analysis"
    FINANCIAL_ANALYSIS = "financial_analysis"
    SALE_PROGRESS_TRACKING = "sale_progress_tracking"
    MARKET_INTELLIGENCE = "market_intelligence"
    CATEGORY_ANALYTICS = "category_analytics"
    PERFORMANCE_METRICS = "performance_metrics"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    TECHNICAL_SPECS = "technical_specs"
    SEMANTIC_SEARCH = "semantic_search"
    UNKNOWN = "unknown"

# Variables d'environnement avec validation
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APP_URL = os.getenv("APP_URL", "https://inventorysbo.onrender.com")

# Variables d'environnement pour Gmail
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "").split(",")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Configuration EODHD (excellente pour actions suisses)
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "687ae6e8493e52.65071366")  # Clé par défaut pour test

# Configuration FreeCurrency (pour conversion USD/EUR vers CHF)
FREECURRENCY_API_KEY = os.getenv("FREECURRENCY_API_KEY", "fca_live_MhoTdTd6auvKD1Dr5kVQ7ua9SwgGPApjylr3CrRe")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    logger.error("Variables d'environnement manquantes")
    raise EnvironmentError("SUPABASE_URL et SUPABASE_KEY sont requis")

logger.info("✅ Variables d'environnement validées")

# Connexions avec gestion d'erreurs
supabase = None
openai_client = None

try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase connecté")
except Exception as e:
    logger.error(f"❌ Erreur Supabase: {e}")
    raise

try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI connecté")
    else:
        logger.warning("⚠️ OpenAI non configuré")
except Exception as e:
    logger.warning(f"⚠️ OpenAI non disponible: {e}")

# Gestionnaire de notifications Gmail avec style exact de la web app
class GmailNotificationManager:
    """Gestionnaire de notifications Gmail avec style identique à la web app"""
    
    def __init__(self):
        self.email_host = EMAIL_HOST
        self.email_port = EMAIL_PORT
        self.email_user = EMAIL_USER
        self.email_password = EMAIL_PASSWORD
        self.recipients = [email.strip() for email in EMAIL_RECIPIENTS if email.strip()]
        self.enabled = bool(EMAIL_USER and EMAIL_PASSWORD and self.recipients)
        self.app_url = APP_URL
        
        if self.enabled:
            logger.info(f"✅ Notifications Gmail activées pour {len(self.recipients)} destinataires")
            logger.info(f"🔗 URL de l'app: {self.app_url}")
        else:
            logger.warning("⚠️ Notifications Gmail désactivées - configuration manquante")
    
    def send_notification_async(self, subject: str, content: str, item_data: Optional[Dict] = None):
        """Envoie une notification de manière asynchrone"""
        if not self.enabled:
            logger.warning("Notifications Gmail désactivées")
            return
        
        # Envoyer dans un thread séparé pour ne pas bloquer l'API
        thread = threading.Thread(
            target=self._send_email,
            args=(subject, content, item_data),
            daemon=True
        )
        thread.start()
    
    def _send_email(self, subject: str, content: str, item_data: Optional[Dict] = None):
        """Envoie effectivement l'email via Gmail"""
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = ", ".join(self.recipients)
            msg['Subject'] = f"[BONVIN Collection] {subject}"
            
            # Contenu HTML avec style exact de la web app
            html_content = self._create_webapp_style_html(subject, content, item_data)
            
            # Attacher le contenu HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Contenu texte de secours
            text_content = self._create_text_content(subject, content, item_data)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Envoyer l'email via Gmail
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"📧 Email Gmail envoyé: {subject}")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi Gmail: {e}")
    
    def _create_webapp_style_html(self, subject: str, content: str, item_data: Optional[Dict] = None) -> str:
        """Crée un HTML avec le style EXACT de la web app"""
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        # Données de l'objet si disponibles
        item_section = ""
        if item_data:
            item_section = self._create_item_details_section(item_data)
        
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --bg-color: #0A232A;
                    --glass-bg: rgba(10, 50, 60, 0.25);
                    --glass-border: rgba(0, 200, 220, 0.2);
                    --glass-glow: rgba(0, 220, 255, 0.15);
                    --text-primary: #e0e6e7;
                    --text-secondary: #88a0a8;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: var(--text-primary);
                    background-color: var(--bg-color);
                    margin: 0;
                    padding: 20px;
                    background-image: 
                        radial-gradient(circle at 15% 25%, rgba(0, 220, 255, 0.2), transparent 40%),
                        radial-gradient(circle at 85% 75%, rgba(10, 50, 60, 0.3), transparent 40%);
                }}
                
                .glass {{
                    background: var(--glass-bg);
                    backdrop-filter: blur(15px);
                    -webkit-backdrop-filter: blur(15px);
                    border: 1px solid var(--glass-border);
                    border-radius: 1.5rem;
                    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
                }}
                
                .glass-dark {{
                    background: rgba(10, 40, 50, 0.4);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid var(--glass-border);
                    border-radius: 1.5rem;
                }}
                
                .glass-subtle {{
                    background: rgba(10, 35, 45, 0.3);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    border: 1px solid var(--glass-border);
                    border-radius: 1.5rem;
                }}
                
                .header-gradient {{
                    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
                    box-shadow: 0 10px 25px rgba(14, 165, 233, 0.3);
                }}
                
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                }}
                
                .main-card {{
                    margin-bottom: 30px;
                    padding: 30px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
                }}
                
                .timestamp-badge {{
                    background: rgba(245, 158, 11, 0.15);
                    border: 1px solid rgba(245, 158, 11, 0.25);
                    color: #fbbf24;
                    padding: 15px;
                    border-radius: 12px;
                    margin: 20px 0;
                    border-left: 4px solid #f59e0b;
                }}
                
                .cta-button {{
                    background: linear-gradient(135deg, #0ea5e9, #0284c7);
                    color: white;
                    text-decoration: none;
                    padding: 12px 24px;
                    border-radius: 12px;
                    font-weight: 600;
                    display: inline-block;
                    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
                    transition: all 0.3s ease;
                }}
                
                .cta-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(14, 165, 233, 0.4);
                }}
                
                /* Status badges - identiques à la web app */
                .status-available {{
                    background: rgba(22, 163, 74, 0.2);
                    border: 1px solid rgba(22, 163, 74, 0.4);
                    color: #4ade80;
                    padding: 6px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 600;
                    display: inline-block;
                }}
                
                .status-sold {{
                    background: rgba(234, 88, 12, 0.2);
                    border: 1px solid rgba(234, 88, 12, 0.4);
                    color: #fb923c;
                    padding: 6px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 600;
                    display: inline-block;
                }}
                
                .status-for-sale {{
                    background: rgba(220, 38, 38, 0.15);
                    border: 1px solid rgba(220, 38, 38, 0.3);
                    color: #f87171;
                    padding: 6px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 600;
                    display: inline-block;
                    animation: pulse-sale 2s infinite;
                }}
                
                .status-sale-progress {{
                    background: rgba(59, 130, 246, 0.2);
                    border: 1px solid rgba(59, 130, 246, 0.4);
                    color: #60a5fa;
                    padding: 6px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 600;
                    display: inline-block;
                }}
                
                @keyframes pulse-sale {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                }}
                
                .item-table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    background: rgba(15, 23, 42, 0.6);
                    border-radius: 12px;
                    overflow: hidden;
                }}
                
                .item-table td {{
                    padding: 12px 16px;
                    border-bottom: 1px solid rgba(0, 200, 220, 0.1);
                }}
                
                .item-table td:first-child {{
                    font-weight: 600;
                    color: var(--text-secondary);
                    width: 40%;
                }}
                
                .item-table tr:last-child td {{
                    border-bottom: none;
                }}
                
                .content-text {{
                    font-size: 16px;
                    line-height: 1.7;
                    margin: 20px 0;
                }}
                
                .footer-card {{
                    text-align: center;
                    padding: 20px;
                    color: var(--text-secondary);
                    font-size: 14px;
                    margin-top: 20px;
                }}
                
                .price-highlight {{
                    font-weight: 700;
                    color: #10b981;
                }}
                
                .offer-highlight {{
                    font-weight: 700;
                    color: #ef4444;
                }}
                
                h1, h2, h3 {{
                    font-weight: 700;
                    color: var(--text-primary);
                }}
                
                .logo-text {{
                    font-size: 28px;
                    font-weight: 800;
                    letter-spacing: 2px;
                    color: white;
                    margin: 0;
                }}
                
                .subtitle {{
                    color: #e0f2fe;
                    margin: 10px 0 0 0;
                    font-size: 16px;
                    font-weight: 500;
                }}
                
                @media (max-width: 600px) {{
                    body {{ padding: 10px; }}
                    .main-card {{ padding: 20px; }}
                    .item-table td {{ padding: 10px 12px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Header avec style exact de la web app -->
                <div class="header-gradient glass" style="padding: 30px; text-align: center; margin-bottom: 30px;">
                    <h1 class="logo-text">BONVIN COLLECTION</h1>
                    <p class="subtitle">Notification de changement</p>
                </div>
                
                <!-- Contenu principal -->
                <div class="glass main-card">
                    <h2 style="margin: 0 0 20px 0; font-size: 22px;">{subject}</h2>
                    
                    <!-- Timestamp -->
                    <div class="timestamp-badge">
                        <strong>📅 {timestamp}</strong>
                    </div>
                    
                    <!-- Contenu -->
                    <div class="content-text">
                        {content.replace(chr(10), '<br>')}
                    </div>
                    
                    <!-- Détails de l'objet -->
                    {item_section}
                    
                    <!-- Call to Action -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.app_url}" class="cta-button">
                            🎯 Accéder au tableau de bord
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="glass footer-card">
                    <p style="margin: 0 0 10px 0;">
                        <strong>Notification automatique BONVIN Collection</strong>
                    </p>
                    <p style="margin: 0; opacity: 0.8;">
                        Email généré automatiquement • <a href="{self.app_url}" style="color: #22d3ee;">Accéder à l'interface</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_item_details_section(self, item_data: Dict) -> str:
        """Crée la section détails avec le style de la web app"""
        details_rows = []
        
        # Nom
        if item_data.get('name'):
            details_rows.append(f'<tr><td>Nom:</td><td><strong>{item_data["name"]}</strong></td></tr>')
        
        # Catégorie
        if item_data.get('category'):
            details_rows.append(f'<tr><td>Catégorie:</td><td>{item_data["category"]}</td></tr>')
        
        # Statut avec badge
        if item_data.get('status'):
            status_class = 'status-available' if item_data['status'] == 'Available' else 'status-sold'
            status_text = 'Disponible' if item_data['status'] == 'Available' else 'Vendu'
            details_rows.append(f'<tr><td>Statut:</td><td><span class="{status_class}">{status_text}</span></td></tr>')
        
        # En vente
        if item_data.get('for_sale'):
            details_rows.append(f'<tr><td>En vente:</td><td><span class="status-for-sale">🔥 EN VENTE</span></td></tr>')
        
        # Statut de vente
        if item_data.get('sale_status'):
            status_label = self._get_sale_status_label_text(item_data['sale_status'])
            details_rows.append(f'<tr><td>Statut vente:</td><td><span class="status-sale-progress">{status_label}</span></td></tr>')
        
        # Prix demandé
        if item_data.get('asking_price'):
            price_formatted = f"{item_data['asking_price']:,.0f} CHF"
            details_rows.append(f'<tr><td>Prix demandé:</td><td><span class="price-highlight">{price_formatted}</span></td></tr>')
        
        # Offre actuelle
        if item_data.get('current_offer'):
            offer_formatted = f"{item_data['current_offer']:,.0f} CHF"
            details_rows.append(f'<tr><td>Offre actuelle:</td><td><span class="offer-highlight">{offer_formatted}</span></td></tr>')
        
        # Prix de vente
        if item_data.get('sold_price'):
            sold_formatted = f"{item_data['sold_price']:,.0f} CHF"
            details_rows.append(f'<tr><td>Vendu pour:</td><td><span class="price-highlight">{sold_formatted}</span></td></tr>')
        
        # Année
        if item_data.get('construction_year'):
            details_rows.append(f'<tr><td>Année:</td><td>{item_data["construction_year"]}</td></tr>')
        
        # Informations spécifiques aux actions
        if item_data.get('category') == 'Actions':
            if item_data.get('stock_symbol'):
                details_rows.append(f'<tr><td>Symbole:</td><td>{item_data["stock_symbol"]}</td></tr>')
            if item_data.get('stock_quantity'):
                details_rows.append(f'<tr><td>Quantité:</td><td>{item_data["stock_quantity"]} actions</td></tr>')
            if item_data.get('stock_exchange'):
                details_rows.append(f'<tr><td>Bourse:</td><td>{item_data["stock_exchange"]}</td></tr>')
        
        # Intermédiaire
        if item_data.get('intermediary'):
            details_rows.append(f'<tr><td>Intermédiaire:</td><td>{item_data["intermediary"]}</td></tr>')
        
        # Détails du progrès
        if item_data.get('sale_progress'):
            progress_text = item_data['sale_progress'][:150] + ('...' if len(item_data['sale_progress']) > 150 else '')
            details_rows.append(f'<tr><td>Détails du progrès:</td><td style="font-style: italic; color: #60a5fa;">{progress_text}</td></tr>')
        
        # Description
        if item_data.get('description'):
            desc_text = item_data['description'][:200] + ('...' if len(item_data['description']) > 200 else '')
            details_rows.append(f'<tr><td>Description:</td><td style="max-width: 300px; word-wrap: break-word;">{desc_text}</td></tr>')
        
        if details_rows:
            return f'''
            <div class="glass-subtle" style="padding: 20px; margin: 20px 0;">
                <h3 style="color: #22d3ee; margin: 0 0 15px 0; font-size: 18px;">📋 Détails de l'objet</h3>
                <table class="item-table">
                    {''.join(details_rows)}
                </table>
            </div>
            '''
        
        return ""
    
    def _get_sale_status_label_text(self, status: str) -> str:
        """Libellés de statut de vente"""
        status_labels = {
            'initial': 'Mise en vente initiale',
            'presentation': 'Préparation présentation',
            'intermediary': 'Choix intermédiaires',
            'inquiries': 'Premières demandes',
            'viewing': 'Visites programmées',
            'negotiation': 'En négociation',
            'offer_received': 'Offre reçue',
            'offer_accepted': 'Offre acceptée',
            'paperwork': 'Formalités en cours',
            'completed': 'Vente finalisée'
        }
        return status_labels.get(status, status)
    
    def _create_text_content(self, subject: str, content: str, item_data: Optional[Dict] = None) -> str:
        """Crée un contenu texte de secours"""
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        text_content = f"""
BONVIN Collection - Notification
================================

{subject}

Date: {timestamp}

{content}
"""
        
        if item_data:
            text_content += f"""

Détails de l'objet:
------------------
Nom: {item_data.get('name', 'N/A')}
Catégorie: {item_data.get('category', 'N/A')}
Statut: {item_data.get('status', 'N/A')}
"""
            if item_data.get('for_sale'):
                text_content += f"En vente: Oui\n"
            if item_data.get('sale_status'):
                text_content += f"Statut vente: {self._get_sale_status_label_text(item_data.get('sale_status', ''))}\n"
            if item_data.get('asking_price'):
                text_content += f"Prix demandé: {item_data.get('asking_price', 0):,.0f} CHF\n"
            if item_data.get('current_offer'):
                text_content += f"Offre actuelle: {item_data.get('current_offer', 0):,.0f} CHF\n"
            if item_data.get('sold_price'):
                text_content += f"Vendu: {item_data.get('sold_price', 0):,.0f} CHF\n"
            if item_data.get('construction_year'):
                text_content += f"Année: {item_data.get('construction_year')}\n"
            if item_data.get('category') == 'Actions':
                if item_data.get('stock_symbol'):
                    text_content += f"Symbole boursier: {item_data.get('stock_symbol')}\n"
                if item_data.get('stock_quantity'):
                    text_content += f"Quantité: {item_data.get('stock_quantity')} actions\n"
            if item_data.get('sale_progress'):
                text_content += f"Détails du progrès: {item_data.get('sale_progress')[:100]}{'...' if len(item_data.get('sale_progress', '')) > 100 else ''}\n"
            if item_data.get('description'):
                text_content += f"Description: {item_data.get('description')[:100]}{'...' if len(item_data.get('description', '')) > 100 else ''}\n"
        
        text_content += f"\n---\nAccéder au tableau de bord: {self.app_url}\nNotification automatique BONVIN Collection"
        
        return text_content
    
    def notify_item_created(self, item_data: Dict):
        """Notification pour un nouvel objet"""
        subject = f"Nouvel objet ajouté: {item_data.get('name', 'Objet sans nom')}"
        content = f"""
🆕 Un nouvel objet vient d'être ajouté à votre collection !

L'objet "<strong>{item_data.get('name', 'N/A')}</strong>" de la catégorie "<strong>{item_data.get('category', 'N/A')}</strong>" a été créé avec succès.

{"🔥 <strong>Cet objet est immédiatement mis en vente !</strong>" if item_data.get('for_sale') else "📦 Cet objet est ajouté à votre inventaire."}

✨ Votre collection compte maintenant un objet de plus !
        """
        self.send_notification_async(subject, content, item_data)
    
    def notify_item_updated(self, old_data: Dict, new_data: Dict):
        """Notification pour une modification d'objet"""
        changes = self._detect_important_changes(old_data, new_data)
        
        if not changes:
            return  # Pas de changements importants
        
        subject = f"Modification: {new_data.get('name', 'Objet')}"
        
        content = f"📝 Des informations importantes ont été mises à jour pour cet objet:\n\n"
        
        for change in changes:
            content += f"• {change}\n"
        
        content += f"\n💡 Consultez le tableau de bord pour voir tous les détails."
        
        self.send_notification_async(subject, content, new_data)
    
    def notify_sale_status_change(self, item_data: Dict, old_status: str, new_status: str):
        """Notification spéciale pour changement de statut de vente"""
        old_label = self._get_sale_status_label_text(old_status)
        new_label = self._get_sale_status_label_text(new_status)
        
        # Émojis selon la progression
        emoji = "📈"
        if new_status in ['offer_received', 'offer_accepted']:
            emoji = "🎯"
        elif new_status == 'negotiation':
            emoji = "🔥"
        elif new_status == 'completed':
            emoji = "🎉"
        
        subject = f"{emoji} Évolution de vente: {item_data.get('name', 'Objet')}"
        
        content = f"""
🚀 Le statut de vente de cet objet vient de progresser !

📊 <strong>Évolution:</strong> "{old_label}" → "<strong>{new_label}</strong>"

{self._get_status_advice(new_status)}

💡 {self._get_next_step_advice(new_status)}
        """
        
        self.send_notification_async(subject, content, item_data)
    
    def notify_new_offer(self, item_data: Dict, offer_amount: float):
        """Notification pour une nouvelle offre"""
        subject = f"💰 Nouvelle offre: {item_data.get('name', 'Objet')}"
        
        asking_price = item_data.get('asking_price', 0)
        percentage = (offer_amount / asking_price * 100) if asking_price > 0 else 0
        
        if percentage >= 90:
            quality = "🔥 <strong>Excellente offre !</strong>"
            advice = "Cette offre est très proche de votre prix demandé. Considérez sérieusement cette proposition."
        elif percentage >= 75:
            quality = "✅ <strong>Offre intéressante</strong>"
            advice = "Cette offre mérite une analyse approfondie. Vous pouvez négocier ou accepter."
        elif percentage >= 50:
            quality = "⚠️ <strong>Offre à négocier</strong>"
            advice = "Cette offre est en dessous de vos attentes. Contre-proposez ou négociez."
        else:
            quality = "❌ <strong>Offre faible</strong>"
            advice = "Cette offre est significativement en dessous du prix demandé. Évaluez si une négociation est pertinente."
        
        content = f"""
💰 Une nouvelle offre vient d'être reçue pour cet objet !

<strong>Montant de l'offre:</strong> {offer_amount:,.0f} CHF
<strong>Prix demandé:</strong> {asking_price:,.0f} CHF  
<strong>Pourcentage:</strong> {percentage:.1f}% du prix demandé

{quality}

💡 <strong>Conseil:</strong> {advice}

⏰ <strong>Prochaine étape:</strong> Analysez cette offre et préparez votre réponse rapidement pour maintenir l'intérêt de l'acheteur.
        """
        
        self.send_notification_async(subject, content, item_data)
    
    def _detect_important_changes(self, old_data: Dict, new_data: Dict) -> List[str]:
        """Détecte les changements importants"""
        changes = []
        
        # Changements de statut
        if old_data.get('status') != new_data.get('status'):
            changes.append(f"<strong>Statut:</strong> {old_data.get('status', 'N/A')} → {new_data.get('status', 'N/A')}")
        
        # Mise en vente
        if old_data.get('for_sale') != new_data.get('for_sale'):
            if new_data.get('for_sale'):
                changes.append("🔥 <strong>Objet mis en vente</strong>")
            else:
                changes.append("📦 <strong>Objet retiré de la vente</strong>")
        
        # Changement de statut de vente
        if old_data.get('sale_status') != new_data.get('sale_status'):
            old_status = self._get_sale_status_label_text(old_data.get('sale_status', ''))
            new_status = self._get_sale_status_label_text(new_data.get('sale_status', ''))
            changes.append(f"<strong>Statut de vente:</strong> {old_status} → {new_status}")
        
        # Changement de détails du progrès
        old_progress = (old_data.get('sale_progress') or '').strip()
        new_progress = (new_data.get('sale_progress') or '').strip()
        
        if old_progress != new_progress:
            if not old_progress and new_progress:
                changes.append(f"📋 <strong>Détails du progrès ajoutés:</strong> {new_progress[:100]}{'...' if len(new_progress) > 100 else ''}")
            elif old_progress and not new_progress:
                changes.append(f"🗑️ <strong>Détails du progrès supprimés</strong>")
            elif old_progress and new_progress:
                changes.append(f"📋 <strong>Détails du progrès modifiés:</strong> {new_progress[:100]}{'...' if len(new_progress) > 100 else ''}")
        
        # Nouvelle offre
        if old_data.get('current_offer') != new_data.get('current_offer'):
            if new_data.get('current_offer'):
                changes.append(f"💰 <strong>Nouvelle offre:</strong> {new_data.get('current_offer', 0):,.0f} CHF")
        
        # Changement de prix
        if old_data.get('asking_price') != new_data.get('asking_price'):
            changes.append(f"<strong>Prix demandé:</strong> {old_data.get('asking_price', 0):,.0f} CHF → {new_data.get('asking_price', 0):,.0f} CHF")
        
        # Prix de vente final
        if old_data.get('sold_price') != new_data.get('sold_price'):
            if new_data.get('sold_price'):
                changes.append(f"🎉 <strong>Vendu pour:</strong> {new_data.get('sold_price', 0):,.0f} CHF")
        
        # Changements spécifiques aux actions
        if new_data.get('category') == 'Actions':
            if old_data.get('stock_quantity') != new_data.get('stock_quantity'):
                changes.append(f"<strong>Quantité d'actions:</strong> {old_data.get('stock_quantity', 0)} → {new_data.get('stock_quantity', 0)}")
            if old_data.get('stock_symbol') != new_data.get('stock_symbol'):
                changes.append(f"<strong>Symbole boursier:</strong> {old_data.get('stock_symbol', 'N/A')} → {new_data.get('stock_symbol', 'N/A')}")
            if old_data.get('current_price') != new_data.get('current_price'):
                changes.append(f"<strong>Prix actuel:</strong> {old_data.get('current_price', 0):,.0f} CHF → {new_data.get('current_price', 0):,.0f} CHF/action")
        
        return changes
    
    def _get_status_advice(self, status: str) -> str:
        """Retourne un conseil selon le statut"""
        advice = {
            'negotiation': "🔥 <strong>Phase critique !</strong> Surveillez les négociations de près et répondez rapidement aux demandes.",
            'offer_received': "💰 <strong>Offre en attente !</strong> Analysez l'offre et préparez votre réponse dans les plus brefs délais.",
            'offer_accepted': "✅ <strong>Félicitations !</strong> L'offre a été acceptée. Préparez les documents pour finaliser la vente.",
            'paperwork': "📋 <strong>Finalisation en cours</strong> Veillez à ce que toutes les formalités soient complétées rapidement.",
            'completed': "🎉 <strong>Vente finalisée avec succès !</strong> Bravo pour cette transaction réussie !"
        }
        return advice.get(status, "📊 Continuez le suivi attentif de cette vente.")
    
    def _get_next_step_advice(self, status: str) -> str:
        """Conseils pour les prochaines étapes"""
        next_steps = {
            'negotiation': "Préparez vos arguments de négociation et définissez votre prix minimum acceptable.",
            'offer_received': "Évaluez l'offre, consultez un expert si nécessaire, et répondez dans les 24-48h.",
            'offer_accepted': "Contactez votre notaire/avocat et préparez tous les documents nécessaires.",
            'paperwork': "Suivez l'avancement des formalités et relancez si nécessaire.",
            'completed': "Archivez les documents et mettez à jour votre comptabilité."
        }
        return f"<strong>Prochaine étape:</strong> {next_steps.get(status, 'Continuez le suivi de cette vente.')}"

# Cache sophistiqué
class SmartCache:
    """Cache intelligent multi-niveaux"""
    
    def __init__(self):
        self._caches = {
            'items': {'data': None, 'timestamp': None, 'ttl': 60},
            'analytics': {'data': None, 'timestamp': None, 'ttl': 300},
            'ai_responses': {'data': {}, 'timestamp': None, 'ttl': 900},
            'embeddings': {'data': {}, 'timestamp': None, 'ttl': 3600}
        }
    
    def get(self, cache_name: str, key: str = 'default'):
        """Récupère du cache"""
        if cache_name not in self._caches:
            return None
        
        cache_info = self._caches[cache_name]
        now = datetime.now()
        
        if cache_info['timestamp'] and (now - cache_info['timestamp']).seconds < cache_info['ttl']:
            if cache_name in ['ai_responses', 'embeddings']:
                return cache_info['data'].get(key)
            return cache_info['data']
        
        return None
    
    def set(self, cache_name: str, data: Any, key: str = 'default'):
        """Stocke dans le cache"""
        if cache_name not in self._caches:
            return
        
        if cache_name in ['ai_responses', 'embeddings']:
            if not isinstance(self._caches[cache_name]['data'], dict):
                self._caches[cache_name]['data'] = {}
            self._caches[cache_name]['data'][key] = data
        else:
            self._caches[cache_name]['data'] = data
        
        self._caches[cache_name]['timestamp'] = datetime.now()
    
    def invalidate(self, cache_name: str = None):
        """Invalide le cache"""
        if cache_name:
            if cache_name in self._caches:
                self._caches[cache_name]['data'] = None if cache_name not in ['ai_responses', 'embeddings'] else {}
                self._caches[cache_name]['timestamp'] = None
        else:
            for cache_info in self._caches.values():
                cache_info['data'] = None
                cache_info['timestamp'] = None

# Instance globale du cache
smart_cache = SmartCache()

# Instance globale du gestionnaire Gmail
gmail_manager = GmailNotificationManager()

# Application Flask
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'bonvin-collection-secret'),
    JSON_SORT_KEYS=False
)
CORS(app)

# Gestionnaire de données sophistiqué
class AdvancedDataManager:
    """Gestionnaire de données avec logique métier avancée"""
    
    @staticmethod
    def fetch_all_items() -> List[CollectionItem]:
        """Récupère tous les objets avec cache"""
        cached_items = smart_cache.get('items')
        if cached_items:
            logger.info(f"📦 Cache: {len(cached_items)} objets")
            return cached_items
        
        try:
            if not supabase:
                return []
            
            response = supabase.table("items").select("*").order("updated_at", desc=True).execute()
            raw_items = response.data or []
            
            items = []
            for raw_item in raw_items:
                try:
                    # Convertir l'embedding du format pgvector
                    if 'embedding' in raw_item and raw_item['embedding']:
                        embedding = raw_item['embedding']
                        
                        # Si c'est une string qui ressemble à un array pgvector
                        if isinstance(embedding, str):
                            # Format pgvector: "[0.1,0.2,0.3]" ou "(0.1,0.2,0.3)"
                            embedding = embedding.strip()
                            if embedding.startswith('[') and embedding.endswith(']'):
                                # Format JSON array
                                try:
                                    raw_item['embedding'] = json.loads(embedding)
                                except:
                                    # Fallback: parser manuellement
                                    raw_item['embedding'] = [float(x) for x in embedding[1:-1].split(',')]
                            elif embedding.startswith('(') and embedding.endswith(')'):
                                # Format pgvector tuple
                                raw_item['embedding'] = [float(x) for x in embedding[1:-1].split(',')]
                            else:
                                logger.warning(f"Format d'embedding inconnu pour {raw_item.get('name', 'item')}: {embedding[:50]}")
                                raw_item['embedding'] = None
                        elif isinstance(embedding, list):
                            # Déjà une liste, parfait
                            pass
                        else:
                            logger.warning(f"Type d'embedding invalide pour {raw_item.get('name', 'item')}: {type(embedding)}")
                            raw_item['embedding'] = None
                    
                    item = CollectionItem.from_dict(raw_item)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Erreur item {raw_item.get('id', '?')}: {e}")
                    continue
            
            smart_cache.set('items', items)
            logger.info(f"🔄 {len(items)} objets chargés")
            return items
            
        except Exception as e:
            logger.error(f"Erreur fetch: {e}")
            return []
    
    @staticmethod
    def calculate_advanced_analytics(items: List[CollectionItem]) -> Dict[str, Any]:
        """Calcule des analytics sophistiquées"""
        cached_analytics = smart_cache.get('analytics')
        if cached_analytics:
            return cached_analytics
        
        analytics = {
            'basic_metrics': AdvancedDataManager._basic_metrics(items),
            'financial_metrics': AdvancedDataManager._financial_metrics(items),
            'category_analytics': AdvancedDataManager._category_analytics(items),
            'sales_pipeline': AdvancedDataManager._sales_pipeline(items),
            'performance_kpis': AdvancedDataManager._performance_kpis(items),
            'market_insights': AdvancedDataManager._market_insights(items),
            'stock_analytics': AdvancedDataManager._stock_analytics(items)
        }
        
        smart_cache.set('analytics', analytics)
        return analytics
    
    @staticmethod
    def _basic_metrics(items: List[CollectionItem]) -> Dict[str, Any]:
        """Métriques de base enrichies"""
        total = len(items)
        available = len([i for i in items if i.status == 'Available'])
        sold = len([i for i in items if i.status == 'Sold'])
        for_sale = len([i for i in items if i.for_sale])
        
        return {
            'total_items': total,
            'available_items': available,
            'sold_items': sold,
            'items_for_sale': for_sale,
            'availability_rate': (available / total * 100) if total > 0 else 0,
            'conversion_rate': (sold / total * 100) if total > 0 else 0,
            'active_sale_rate': (for_sale / available * 100) if available > 0 else 0
        }
    
    @staticmethod
    def _financial_metrics(items: List[CollectionItem]) -> Dict[str, Any]:
        """Métriques financières avancées"""
        total_asking = sum(i.asking_price or 0 for i in items if i.status == 'Available' and i.asking_price)
        total_sold = sum(i.sold_price or 0 for i in items if i.status == 'Sold' and i.sold_price)
        total_acquisition = sum(i.acquisition_price or 0 for i in items if i.acquisition_price)
        
        # ROI calculation
        profit_items = [
            (i.sold_price or 0) - (i.acquisition_price or 0)
            for i in items 
            if i.status == 'Sold' and i.sold_price and i.acquisition_price
        ]
        
        total_profit = sum(profit_items)
        roi_percentage = (total_profit / total_acquisition * 100) if total_acquisition > 0 else 0
        
        return {
            'portfolio_value': total_asking,
            'realized_sales': total_sold,
            'total_acquisition_cost': total_acquisition,
            'total_profit': total_profit,
            'roi_percentage': roi_percentage,
            'average_item_value': total_asking / len([i for i in items if i.asking_price]) if any(i.asking_price for i in items) else 0,
            'profit_margin': (total_profit / total_sold * 100) if total_sold > 0 else 0
        }
    
    @staticmethod
    def _category_analytics(items: List[CollectionItem]) -> Dict[str, Any]:
        """Analytics par catégorie"""
        categories = {}
        
        for item in items:
            cat = item.category or 'Uncategorized'
            if cat not in categories:
                categories[cat] = {
                    'total': 0, 'available': 0, 'sold': 0, 'for_sale': 0,
                    'total_value': 0, 'avg_value': 0
                }
            
            stats = categories[cat]
            stats['total'] += 1
            
            if item.status == 'Available':
                stats['available'] += 1
            elif item.status == 'Sold':
                stats['sold'] += 1
            
            if item.for_sale:
                stats['for_sale'] += 1
            
            value = item.asking_price or item.sold_price or 0
            stats['total_value'] += value
        
        # Calculer les moyennes
        for stats in categories.values():
            if stats['total'] > 0:
                stats['avg_value'] = stats['total_value'] / stats['total']
        
        return categories
    
    @staticmethod
    def _sales_pipeline(items: List[CollectionItem]) -> Dict[str, Any]:
        """Pipeline de vente sophistiqué"""
        pipeline_stages = {
            'initial': 'Mise en vente initiale',
            'presentation': 'Préparation présentation',
            'intermediary': 'Choix intermédiaires',
            'inquiries': 'Premières demandes',
            'viewing': 'Visites programmées',
            'negotiation': 'En négociation',
            'offer_received': 'Offres reçues',
            'offer_accepted': 'Offres acceptées',
            'paperwork': 'Formalités en cours',
            'completed': 'Ventes finalisées'
        }
        
        pipeline_data = {}
        total_value = 0
        
        for stage_key, stage_name in pipeline_stages.items():
            stage_items = [i for i in items if i.for_sale and i.sale_status == stage_key]
            stage_value = sum(i.asking_price or 0 for i in stage_items)
            
            pipeline_data[stage_key] = {
                'name': stage_name,
                'count': len(stage_items),
                'total_value': stage_value,
                'items': [{'name': i.name, 'value': i.asking_price} for i in stage_items]
            }
            total_value += stage_value
        
        return {
            'stages': pipeline_data,
            'total_pipeline_value': total_value,
            'active_negotiations': len([i for i in items if i.for_sale and i.sale_status in ['negotiation', 'offer_received']])
        }
    
    @staticmethod
    def _performance_kpis(items: List[CollectionItem]) -> Dict[str, Any]:
        """KPIs de performance"""
        # Top performers par valeur
        top_sales = sorted(
            [i for i in items if i.sold_price], 
            key=lambda x: x.sold_price, 
            reverse=True
        )[:5]
        
        # Distribution des prix
        prices = [i.sold_price or i.asking_price for i in items if i.sold_price or i.asking_price]
        price_ranges = {
            'under_100k': len([p for p in prices if p < 100000]),
            '100k_500k': len([p for p in prices if 100000 <= p < 500000]),
            '500k_1m': len([p for p in prices if 500000 <= p < 1000000]),
            'over_1m': len([p for p in prices if p >= 1000000])
        }
        
        return {
            'top_value_sales': [{'name': i.name, 'value': i.sold_price} for i in top_sales],
            'price_distribution': price_ranges,
            'inventory_turnover': len([i for i in items if i.status == 'Sold']) / len(items) if items else 0
        }
    
    @staticmethod
    def _market_insights(items: List[CollectionItem]) -> Dict[str, Any]:
        """Insights de marché"""
        # Hotness par catégorie (basé sur l'activité)
        category_activity = {}
        
        for item in items:
            cat = item.category or 'Other'
            if cat not in category_activity:
                category_activity[cat] = 0
            
            # Score d'activité
            if item.for_sale:
                category_activity[cat] += 2
            if item.sale_status in ['negotiation', 'offer_received']:
                category_activity[cat] += 5
            if item.status == 'Sold':
                category_activity[cat] += 3
        
        return {
            'category_activity_scores': category_activity,
            'most_active_category': max(category_activity.items(), key=lambda x: x[1])[0] if category_activity else None,
            'market_temperature': 'hot' if max(category_activity.values(), default=0) > 10 else 'warm' if max(category_activity.values(), default=0) > 5 else 'cool'
        }
    
    @staticmethod
    def _stock_analytics(items: List[CollectionItem]) -> Dict[str, Any]:
        """Analytics spécifiques aux actions"""
        stock_items = [i for i in items if i.category == 'Actions']
        
        if not stock_items:
            return {
                'total_stocks': 0,
                'total_shares': 0,
                'total_value': 0,
                'by_exchange': {},
                'top_holdings': []
            }
        
        total_shares = sum(i.stock_quantity or 0 for i in stock_items)
        total_value = sum(i.asking_price or 0 for i in stock_items)
        
        # Grouper par bourse
        by_exchange = {}
        for item in stock_items:
            exchange = item.stock_exchange or 'Unknown'
            if exchange not in by_exchange:
                by_exchange[exchange] = {'count': 0, 'value': 0}
            by_exchange[exchange]['count'] += 1
            by_exchange[exchange]['value'] += item.asking_price or 0
        
        # Top holdings par valeur
        top_holdings = sorted(
            stock_items,
            key=lambda x: x.asking_price or 0,
            reverse=True
        )[:5]
        
        return {
            'total_stocks': len(stock_items),
            'total_shares': total_shares,
            'total_value': total_value,
            'average_holding_value': total_value / len(stock_items) if stock_items else 0,
            'by_exchange': by_exchange,
            'top_holdings': [
                {
                    'symbol': h.stock_symbol,
                    'name': h.name,
                    'quantity': h.stock_quantity,
                    'value': h.asking_price
                }
                for h in top_holdings
            ]
        }

# Classe pour la recherche sémantique RAG
class SemanticSearchRAG:
    """Moteur de recherche sémantique avec RAG"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.embedding_model = "text-embedding-3-small"
    
    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Génère l'embedding pour une requête"""
        if not self.client:
            return None
        
        try:
            response = self.client.embeddings.create(
                input=query,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erreur génération embedding: {e}")
            return None
    
    def semantic_search(self, query: str, items: List[CollectionItem], top_k: int = 10) -> List[Tuple[CollectionItem, float]]:
        """Recherche sémantique dans les items"""
        query_embedding = self.get_query_embedding(query)
        if not query_embedding:
            logger.warning("Impossible de générer l'embedding pour la requête")
            return []
        
        # Vérifier combien d'items ont des embeddings
        items_with_embeddings = [item for item in items if item.embedding]
        logger.info(f"Items avec embeddings: {len(items_with_embeddings)}/{len(items)}")
        
        if not items_with_embeddings:
            logger.error("Aucun item n'a d'embedding ! La recherche sémantique ne peut pas fonctionner.")
            return []
        
        # Calculer les similarités cosinus
        similarities = []
        for item in items_with_embeddings:
            try:
                similarity = self._cosine_similarity(query_embedding, item.embedding)
                similarities.append((item, similarity))
            except Exception as e:
                logger.warning(f"Erreur calcul similarité pour {item.name}: {e}")
                continue
        
        # Trier par similarité décroissante
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Retourner top_k résultats
        return similarities[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        vec1_np = np.array(vec1).reshape(1, -1)
        vec2_np = np.array(vec2).reshape(1, -1)
        return cosine_similarity(vec1_np, vec2_np)[0][0]
    
    def generate_embedding_for_item(self, item: CollectionItem) -> Optional[List[float]]:
        """Génère l'embedding pour un item"""
        if not self.client:
            return None
        
        # Créer le texte à encoder - INCLURE LES INFOS ACTIONS
        text_parts = [
            f"Nom: {item.name}",
            f"Catégorie: {item.category}",
            f"Statut: {item.status}",
        ]
        
        if item.construction_year:
            text_parts.append(f"Année: {item.construction_year}")
        
        if item.condition:
            text_parts.append(f"État: {item.condition}")
        
        if item.description:
            text_parts.append(f"Description: {item.description}")
        
        if item.for_sale:
            text_parts.append("En vente actuellement")
        
        if item.sale_status:
            text_parts.append(f"Statut de vente: {item.sale_status}")
        
        if item.asking_price:
            text_parts.append(f"Prix demandé: {item.asking_price} CHF")
        
        if item.sold_price:
            text_parts.append(f"Prix de vente: {item.sold_price} CHF")
        
        # Informations spécifiques aux actions
        if item.category == 'Actions':
            if item.stock_symbol:
                text_parts.append(f"Symbole boursier: {item.stock_symbol}")
            if item.stock_quantity:
                text_parts.append(f"Quantité: {item.stock_quantity} actions")
            if item.stock_exchange:
                text_parts.append(f"Bourse: {item.stock_exchange}")
            if item.current_price:
                text_parts.append(f"Prix actuel: {item.current_price} CHF")
        
        text = ". ".join(text_parts)
        
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erreur génération embedding item: {e}")
            return None

# Moteur d'IA OpenAI Pure avec RAG
class PureOpenAIEngineWithRAG:
    """Moteur d'IA utilisant OpenAI GPT-4 avec recherche sémantique RAG"""
    
    def __init__(self, client):
        self.client = client
        self.semantic_search = SemanticSearchRAG(client) if client else None
    
    def detect_query_intent(self, query: str) -> QueryIntent:
        """Détecte l'intention de la requête"""
        query_lower = query.lower()
        
        # Mots-clés pour la recherche sémantique - ÉLARGI
        semantic_keywords = [
            'trouve', 'cherche', 'montre', 'affiche', 'liste',
            'combien', 'quel', 'quels', 'quelle', 'quelles',
            'où', 'qui', 'avec', 'comme', 'similaire',
            'ai-je', 'j\'ai', 'mes', 'ma', 'mon',
            'allemande', 'italienne', 'française', 'japonaise',
            'porsche', 'ferrari', 'lamborghini', 'bmw', 'mercedes',
            'actions', 'bourse', 'portefeuille', 'symbole'
        ]
        
        # Forcer la recherche sémantique pour les questions sur les quantités et marques
        if 'combien' in query_lower or any(word in query_lower for word in ['porsche', 'allemande', 'italienne', 'actions', 'bourse']):
            logger.info(f"Intent détecté: SEMANTIC_SEARCH pour '{query}'")
            return QueryIntent.SEMANTIC_SEARCH
        
        # Vérifier si c'est une recherche sémantique
        if any(keyword in query_lower for keyword in semantic_keywords):
            logger.info(f"Intent détecté: SEMANTIC_SEARCH pour '{query}'")
            return QueryIntent.SEMANTIC_SEARCH
        
        # Autres intentions existantes
        if any(word in query_lower for word in ['vente', 'négociation', 'offre', 'pipeline']):
            return QueryIntent.SALE_PROGRESS_TRACKING
        
        if any(word in query_lower for word in ['financ', 'roi', 'profit', 'rentab']):
            return QueryIntent.FINANCIAL_ANALYSIS
        
        if any(word in query_lower for word in ['voiture', 'montre', 'bateau', 'avion']):
            return QueryIntent.VEHICLE_ANALYSIS
        
        return QueryIntent.UNKNOWN
    
    def generate_response(self, query: str, items: List[CollectionItem], analytics: Dict[str, Any]) -> str:
        """Génère une réponse via OpenAI GPT-4 avec RAG"""
        
        if not self.client:
            return "❌ Moteur IA Indisponible"
        
        # Toujours utiliser la recherche sémantique si on a des embeddings
        items_with_embeddings = sum(1 for item in items if item.embedding)
        if items_with_embeddings > 0:
            logger.info(f"Utilisation de la recherche sémantique pour: '{query}'")
            return self._generate_semantic_response(query, items, analytics)
        
        # Sinon fallback sur l'ancienne méthode
        logger.info(f"Pas d'embeddings, utilisation de la méthode classique")
        
        # Cache et méthode classique...
        cache_key = hashlib.md5(f"{query}{len(items)}{json.dumps(analytics.get('basic_metrics', {}), sort_keys=True)}".encode()).hexdigest()[:12]
        cached_response = smart_cache.get('ai_responses', cache_key)
        if cached_response:
            return cached_response
        
        try:
            # Construire le contexte complet
            context = self._build_complete_context(items, analytics)
            
            # Prompt système unifié
            system_prompt = """Tu es l'assistant IA expert de la collection BONVIN.
Tu as accès à toutes les données de la collection et tu fournis des analyses précises et contextualisées.
Tu réponds TOUJOURS en français de manière STRUCTURÉE et CONCISE.

RÈGLES:
1. Utilise TOUJOURS des données factuelles de la collection
2. Structure tes réponses avec des titres et des listes
3. Sois PRÉCIS avec les chiffres et les détails
4. Maximum 800 mots
5. Pas de formules de politesse génériques
6. Utilise ton intelligence pour comprendre et contextualiser les données"""

            # Prompt utilisateur
            user_prompt = f"""QUESTION: {query}

DONNÉES COLLECTION BONVIN:
{context}

Analyse cette question et fournis une réponse complète et contextualisée basée sur les données réelles de la collection.
Si la question concerne des véhicules, utilise ton intelligence pour déterminer leurs caractéristiques.
Sois créatif dans ton analyse tout en restant factuel."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
                timeout=30
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Cache la réponse
            smart_cache.set('ai_responses', ai_response, cache_key)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Erreur OpenAI: {e}")
            return "❌ Moteur IA Indisponible"
    
    def _generate_semantic_response(self, query: str, items: List[CollectionItem], analytics: Dict[str, Any]) -> str:
        """Génère une réponse en utilisant la recherche sémantique RAG"""
        try:
            # Vérifier d'abord si nous avons des embeddings
            items_with_embeddings = sum(1 for item in items if item.embedding)
            logger.info(f"Recherche sémantique - Items avec embeddings: {items_with_embeddings}/{len(items)}")
            
            if items_with_embeddings == 0:
                logger.warning("Aucun embedding disponible, bascule sur recherche par mots-clés")
                return self._fallback_to_keyword_search(query, items)
            
            # Recherche sémantique
            semantic_results = self.semantic_search.semantic_search(query, items, top_k=15)
            
            if not semantic_results:
                logger.warning("Pas de résultats sémantiques, bascule sur recherche par mots-clés")
                return self._fallback_to_keyword_search(query, items)
            
            # Filtrer les résultats pertinents (score > 0.5 au lieu de 0.7)
            relevant_results = [(item, score) for item, score in semantic_results if score > 0.5]
            
            if not relevant_results:
                # Si pas de résultats très pertinents, prendre les 10 meilleurs
                relevant_results = semantic_results[:10]
            
            logger.info(f"Résultats sémantiques trouvés: {len(relevant_results)} items pertinents")
            
            # Construire le contexte RAG
            rag_context = self._build_rag_context(relevant_results, query)
            
            # Prompt pour GPT avec contexte RAG
            system_prompt = """Tu es l'assistant IA expert de la collection BONVIN avec capacités de recherche sémantique avancée.
Tu utilises les résultats de recherche sémantique pour fournir des réponses précises et contextualisées.

RÈGLES IMPORTANTES:
1. Base-toi sur les objets trouvés par la recherche sémantique
2. Si les scores sont faibles (<0.6), mentionne que la recherche est approximative
3. Structure ta réponse de manière claire avec des catégories
4. Sois intelligent dans l'interprétation - par exemple:
   - "montres" = chercher dans la catégorie Montres
   - "en vente" = objets avec for_sale = true
   - "chers" = objets avec prix élevé
   - Noms de marques = chercher ces marques spécifiquement
   - "actions" = chercher dans la catégorie Actions
   - "portefeuille" = analyser les actions et investissements
5. Utilise ton bon sens pour comprendre l'intention de l'utilisateur
6. Si peu de résultats pertinents, élargis ta recherche
7. Toujours donner le nombre exact trouvé
8. Pour les questions de prix/valeur, additionne et calcule les totaux
9. Pour les actions, mentionne le symbole boursier et la quantité si disponibles"""

            user_prompt = f"""RECHERCHE DEMANDÉE: {query}

RÉSULTATS DE LA RECHERCHE SÉMANTIQUE (Triés par pertinence):
{rag_context}

STATISTIQUES GLOBALES:
- Total objets dans la collection: {len(items)}
- Objets trouvés par la recherche: {len(relevant_results)}
- Score de pertinence moyen: {sum(score for _, score in relevant_results) / len(relevant_results):.2f}

Analyse ces résultats et réponds à la recherche de l'utilisateur de manière complète et structurée.
Si la recherche concerne des caractéristiques spécifiques (ex: "voitures 4 places"), utilise ton intelligence pour identifier ces caractéristiques."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1200,
                timeout=30
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Ajouter un indicateur de recherche sémantique
            ai_response = f"🔍 **Recherche intelligente activée**\n\n{ai_response}"
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Erreur recherche sémantique: {e}")
            return self._fallback_to_keyword_search(query, items)
    
    def _build_rag_context(self, results: List[Tuple[CollectionItem, float]], query: str) -> str:
        """Construit le contexte pour RAG"""
        context_parts = []
        
        for i, (item, score) in enumerate(results, 1):
            context_parts.append(f"\n{i}. **{item.name}** (Pertinence: {score:.2%})")
            context_parts.append(f"   - Catégorie: {item.category}")
            context_parts.append(f"   - Statut: {'Disponible' if item.status == 'Available' else 'Vendu'}")
            
            if item.for_sale:
                context_parts.append(f"   - 🔥 EN VENTE")
                if item.sale_status:
                    context_parts.append(f"   - Progression vente: {item.sale_status}")
            
            if item.construction_year:
                context_parts.append(f"   - Année: {item.construction_year}")
            
            if item.condition:
                context_parts.append(f"   - État: {item.condition}")
            
            if item.asking_price:
                context_parts.append(f"   - Prix demandé: {item.asking_price:,.0f} CHF")
            
            if item.sold_price:
                context_parts.append(f"   - Prix de vente: {item.sold_price:,.0f} CHF")
            
            if item.current_offer:
                context_parts.append(f"   - Offre actuelle: {item.current_offer:,.0f} CHF")
            
            # Informations spécifiques aux actions
            if item.category == 'Actions':
                if item.stock_symbol:
                    context_parts.append(f"   - Symbole boursier: {item.stock_symbol}")
                if item.stock_quantity:
                    context_parts.append(f"   - Quantité: {item.stock_quantity} actions")
                if item.stock_exchange:
                    context_parts.append(f"   - Bourse: {item.stock_exchange}")
                if item.stock_purchase_price:
                    context_parts.append(f"   - Prix d'achat unitaire: {item.stock_purchase_price:,.0f} CHF")
                if item.current_price:
                    context_parts.append(f"   - Prix actuel: {item.current_price:,.0f} CHF/action")
            
            if item.description:
                # Extraire les parties pertinentes de la description
                desc_preview = item.description[:150] + "..." if len(item.description) > 150 else item.description
                context_parts.append(f"   - Description: {desc_preview}")
            
            # Informations spécifiques selon la catégorie
            if item.category == "Appartements / maison" and item.surface_m2:
                context_parts.append(f"   - Surface: {item.surface_m2} m²")
                if item.rental_income_chf:
                    context_parts.append(f"   - Revenus locatifs: {item.rental_income_chf:,.0f} CHF/mois")
        
        return "\n".join(context_parts)
    
    def _fallback_to_keyword_search(self, query: str, items: List[CollectionItem]) -> str:
        """Recherche par mots-clés si la recherche sémantique échoue"""
        query_lower = query.lower()
        
        # Détecter les intentions spécifiques
        car_brands = {
            'allemandes': ['porsche', 'bmw', 'mercedes', 'audi', 'volkswagen'],
            'italiennes': ['ferrari', 'lamborghini', 'maserati', 'alfa romeo'],
            'françaises': ['peugeot', 'renault', 'citroën', 'bugatti'],
            'japonaises': ['toyota', 'honda', 'nissan', 'mazda', 'lexus'],
            'anglaises': ['rolls', 'bentley', 'aston martin', 'jaguar', 'mini']
        }
        
        # Recherche intelligente selon le contexte
        matching_items = []
        
        # Recherche spécifique pour les actions
        if 'action' in query_lower or 'bourse' in query_lower or 'portefeuille' in query_lower:
            matching_items = [item for item in items if item.category == "Actions"]
        else:
            # Recherche par mots-clés standard
            keywords = query_lower.split()
            for item in items:
                item_text = f"{item.name} {item.category} {item.description or ''} {item.status}".lower()
                if item.stock_symbol:
                    item_text += f" {item.stock_symbol}".lower()
                if any(keyword in item_text for keyword in keywords):
                    matching_items.append(item)
        
        if not matching_items:
            return f"""
🔍 **Aucun résultat trouvé**

Je n'ai trouvé aucun objet correspondant à votre recherche "{query}".

💡 **Note importante:** Il semble que les embeddings ne soient pas correctement configurés. 
Pour une recherche intelligente optimale, assurez-vous que tous les objets ont des embeddings générés.

📊 **Statistiques rapides:**
- Total objets: {len(items)}
- Catégories disponibles: {', '.join(set(i.category for i in items if i.category))}
"""
        
        # Construire la réponse
        response_parts = [f"🔍 **Résultats pour:** {query}\n"]
        response_parts.append(f"J'ai trouvé **{len(matching_items)} objets**:\n")
        
        # Grouper par catégorie
        by_category = {}
        for item in matching_items:
            cat = item.category or "Autre"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)
        
        for category, cat_items in by_category.items():
            response_parts.append(f"\n**{category}** ({len(cat_items)} objets):")
            for item in cat_items[:5]:
                status = "✅ Disponible" if item.status == "Available" else "🏷️ Vendu"
                price = ""
                if item.asking_price:
                    price = f" - {item.asking_price:,.0f} CHF"
                elif item.sold_price:
                    price = f" - Vendu: {item.sold_price:,.0f} CHF"
                
                for_sale = " 🔥 EN VENTE" if item.for_sale else ""
                response_parts.append(f"- {item.name} ({item.construction_year or 'N/A'}) {status}{price}{for_sale}")
                
                # Détails spécifiques aux actions
                if item.category == "Actions" and item.stock_symbol:
                    response_parts.append(f"  → Symbole: {item.stock_symbol}, Quantité: {item.stock_quantity or 'N/A'}")
                    if item.current_price:
                        response_parts.append(f"  → Prix actuel: {item.current_price:,.0f} CHF/action")
            
            if len(cat_items) > 5:
                response_parts.append(f"  ... et {len(cat_items) - 5} autres")
        
        return "\n".join(response_parts)
    
    def _build_complete_context(self, items: List[CollectionItem], analytics: Dict[str, Any]) -> str:
        """Construit un contexte complet pour l'IA"""
        context_parts = []
        
        # Vue d'ensemble
        basic = analytics.get('basic_metrics', {})
        context_parts.append(f"=== VUE D'ENSEMBLE ===")
        context_parts.append(f"Total objets: {basic.get('total_items', 0)}")
        context_parts.append(f"Disponibles: {basic.get('available_items', 0)}")
        context_parts.append(f"Vendus: {basic.get('sold_items', 0)}")
        context_parts.append(f"En vente: {basic.get('items_for_sale', 0)}")
        
        # Métriques financières
        financial = analytics.get('financial_metrics', {})
        context_parts.append(f"\n=== MÉTRIQUES FINANCIÈRES ===")
        context_parts.append(f"Valeur portefeuille: {financial.get('portfolio_value', 0):,.0f} CHF")
        context_parts.append(f"CA réalisé: {financial.get('realized_sales', 0):,.0f} CHF")
        context_parts.append(f"ROI: {financial.get('roi_percentage', 0):.1f}%")
        context_parts.append(f"Profit total: {financial.get('total_profit', 0):,.0f} CHF")
        
        # Analytics actions si disponibles
        stock_analytics = analytics.get('stock_analytics', {})
        if stock_analytics.get('total_stocks', 0) > 0:
            context_parts.append(f"\n=== PORTEFEUILLE ACTIONS ===")
            context_parts.append(f"Nombre d'actions différentes: {stock_analytics.get('total_stocks', 0)}")
            context_parts.append(f"Total actions détenues: {stock_analytics.get('total_shares', 0)}")
            context_parts.append(f"Valeur totale: {stock_analytics.get('total_value', 0):,.0f} CHF")
        
        # Liste détaillée des objets
        context_parts.append(f"\n=== INVENTAIRE DÉTAILLÉ ===")
        
        # Grouper par catégorie
        categories = {}
        for item in items:
            cat = item.category or 'Autre'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        for category, cat_items in categories.items():
            context_parts.append(f"\n{category.upper()} ({len(cat_items)} objets):")
            
            # Trier par statut
            for_sale = [i for i in cat_items if i.for_sale]
            available = [i for i in cat_items if i.status == 'Available' and not i.for_sale]
            sold = [i for i in cat_items if i.status == 'Sold']
            
            if for_sale:
                context_parts.append("EN VENTE:")
                for item in for_sale:
                    context_parts.append(f"- {item.name} ({item.construction_year or 'N/A'})")
                    if item.asking_price:
                        context_parts.append(f"  Prix: {item.asking_price:,.0f} CHF")
                    if item.sale_status:
                        context_parts.append(f"  Statut: {item.sale_status}")
                    if item.current_offer:
                        context_parts.append(f"  Offre actuelle: {item.current_offer:,.0f} CHF")
                    # Détails spécifiques aux actions
                    if item.category == 'Actions' and item.stock_symbol:
                        context_parts.append(f"  Symbole: {item.stock_symbol}")
                        context_parts.append(f"  Quantité: {item.stock_quantity} actions")
                        if item.current_price:
                            context_parts.append(f"  Prix actuel: {item.current_price:,.0f} CHF/action")
            
            if available:
                context_parts.append("DISPONIBLES:")
                for item in available[:5]:  # Limiter pour ne pas surcharger
                    context_parts.append(f"- {item.name} ({item.construction_year or 'N/A'})")
                    if item.category == 'Actions' and item.stock_symbol:
                        context_parts.append(f"  → {item.stock_symbol}: {item.stock_quantity} actions")
                        if item.current_price:
                            context_parts.append(f"  → Prix actuel: {item.current_price:,.0f} CHF/action")
                if len(available) > 5:
                    context_parts.append(f"... et {len(available) - 5} autres")
            
            if sold:
                context_parts.append("VENDUS:")
                for item in sold[:3]:  # Limiter
                    context_parts.append(f"- {item.name}")
                    if item.sold_price:
                        context_parts.append(f"  Vendu: {item.sold_price:,.0f} CHF")
                if len(sold) > 3:
                    context_parts.append(f"... et {len(sold) - 3} autres")
        
        # Pipeline de vente
        pipeline = analytics.get('sales_pipeline', {})
        if pipeline.get('stages'):
            context_parts.append(f"\n=== PIPELINE DE VENTE ===")
            for stage_data in pipeline['stages'].values():
                if stage_data['count'] > 0:
                    context_parts.append(f"{stage_data['name']}: {stage_data['count']} objets ({stage_data['total_value']:,.0f} CHF)")
        
        return "\n".join(context_parts)

# Instance du moteur IA avec RAG
ai_engine = PureOpenAIEngineWithRAG(openai_client) if openai_client else None

# Routes
@app.route("/")
def index():
    """Page principale de l'application"""
    return render_template('index.html')

@app.route("/analytics")
def analytics():
    """Page analytics avec diagrammes et statistiques"""
    return render_template('analytics.html')

@app.route("/health")
def health():
    """Health check"""
    try:
        items = AdvancedDataManager.fetch_all_items()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "app_url": APP_URL,
            "services": {
                "supabase": "connected" if supabase else "disconnected",
                "openai": "connected" if openai_client else "disconnected",
                "ai_engine": "active_with_rag" if ai_engine else "inactive",
                "gmail_notifications": "enabled" if gmail_manager.enabled else "disabled",
                "finnhub": "configured" if FINNHUB_API_KEY else "not_configured"
            },
            "data_status": {
                "items_count": len(items),
                "cache_active": smart_cache._caches['items']['data'] is not None,
                "last_update": items[0].updated_at if items else None,
                "embeddings_ready": sum(1 for item in items if item.embedding) if items else 0,
                "stocks_count": len([i for i in items if i.category == "Actions"])
            },
            "ai_mode": "openai_gpt4_with_semantic_rag",
            "stock_apis": {
                "yahoo_finance": "available",
                "finnhub": "configured" if FINNHUB_API_KEY else "not_configured"
            }
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Erreur health: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/analytics/advanced")
def advanced_analytics():
    """Analytics sophistiquées"""
    try:
        items = AdvancedDataManager.fetch_all_items()
        analytics = AdvancedDataManager.calculate_advanced_analytics(items)
        
        return jsonify({
            "analytics": analytics,
            "metadata": {
                "items_analyzed": len(items),
                "generated_at": datetime.now().isoformat(),
                "cache_status": "hit" if smart_cache.get('analytics') else "miss"
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur analytics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/items", methods=["GET"])
def get_items():
    """Récupère tous les objets"""
    try:
        items = AdvancedDataManager.fetch_all_items()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        logger.error(f"Erreur get_items: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/items", methods=["POST"])
def create_item():
    """Crée un objet avec notification Gmail et génération d'embedding"""
    if not supabase:
        return jsonify({"error": "Supabase non connecté"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        # Validation spécifique pour les actions
        if data.get('category') == 'Actions':
            if not data.get('stock_symbol'):
                return jsonify({"error": "Le symbole boursier est requis pour les actions"}), 400
        
        # Enrichissement
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        
        # Générer l'embedding si OpenAI disponible
        if ai_engine and ai_engine.semantic_search:
            # Ajouter un ID temporaire pour créer l'objet
            temp_data = data.copy()
            temp_data['id'] = 0  # ID temporaire pour la création de l'objet
            temp_item = CollectionItem.from_dict(temp_data)
            embedding = ai_engine.semantic_search.generate_embedding_for_item(temp_item)
            if embedding:
                data['embedding'] = embedding
                logger.info("✅ Embedding généré pour le nouvel objet")
        
        # Ne pas inclure l'ID dans l'insertion Supabase
        if 'id' in data:
            del data['id']
        
        response = supabase.table("items").insert(data).execute()
        if response.data:
            smart_cache.invalidate('items')
            smart_cache.invalidate('analytics')
            
            # Notification Gmail pour nouvel objet
            gmail_manager.notify_item_created(response.data[0])
            
            return jsonify(response.data[0]), 201
        else:
            return jsonify({"error": "Erreur lors de la création"}), 500
            
    except Exception as e:
        logger.error(f"Erreur création item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Met à jour un objet avec notifications Gmail et mise à jour de l'embedding"""
    if not supabase:
        return jsonify({"error": "Supabase non connecté"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        # Récupérer l'ancien état avant modification
        old_response = supabase.table("items").select("*").eq("id", item_id).execute()
        old_data = old_response.data[0] if old_response.data else {}
        
        # Nettoyage sophistiqué des données
        cleaned_data = clean_update_data(data)
        cleaned_data['updated_at'] = datetime.now().isoformat()
        
        # Vérifier si l'embedding doit être mis à jour
        should_update_embedding = False
        embedding_fields = ['name', 'category', 'description', 'status', 'construction_year', 
                          'condition', 'for_sale', 'sale_status', 'stock_symbol', 'stock_quantity', 'current_price',
        'stock_volume', 'stock_pe_ratio', 'stock_52_week_high', 'stock_52_week_low',
        'stock_change', 'stock_change_percent', 'stock_average_volume']
        
        for field in embedding_fields:
            if field in cleaned_data and old_data.get(field) != cleaned_data.get(field):
                should_update_embedding = True
                break
        
        # Mettre à jour l'embedding si nécessaire
        if should_update_embedding and ai_engine and ai_engine.semantic_search:
            # Créer un item temporaire avec les nouvelles données
            temp_data = {**old_data, **cleaned_data}
            temp_item = CollectionItem.from_dict(temp_data)
            new_embedding = ai_engine.semantic_search.generate_embedding_for_item(temp_item)
            if new_embedding:
                cleaned_data['embedding'] = new_embedding
                logger.info(f"✅ Embedding mis à jour pour l'objet {item_id}")
        
        response = supabase.table("items").update(cleaned_data).eq("id", item_id).execute()
        
        if response.data:
            smart_cache.invalidate('items')
            smart_cache.invalidate('analytics')
            
            new_data = response.data[0]
            
            # Notifications Gmail selon les changements
            
            # Changement de statut de vente spécifique
            if old_data.get('sale_status') != new_data.get('sale_status') and new_data.get('for_sale'):
                gmail_manager.notify_sale_status_change(
                    new_data, 
                    old_data.get('sale_status', ''), 
                    new_data.get('sale_status', '')
                )
            
            # Nouvelle offre
            elif old_data.get('current_offer') != new_data.get('current_offer') and new_data.get('current_offer'):
                gmail_manager.notify_new_offer(new_data, new_data.get('current_offer'))
            
            # Autres changements importants
            else:
                gmail_manager.notify_item_updated(old_data, new_data)
            
            return jsonify(new_data)
        else:
            return jsonify({"error": f"Objet {item_id} non trouvé"}), 404
            
    except Exception as e:
        logger.error(f"Erreur update_item {item_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Supprime un objet"""
    if not supabase:
        return jsonify({"error": "Supabase non connecté"}), 500
    
    try:
        response = supabase.table("items").delete().eq("id", item_id).execute()
        smart_cache.invalidate('items')
        smart_cache.invalidate('analytics')
        return "", 204
    except Exception as e:
        logger.error(f"Erreur delete_item: {e}")
        return jsonify({"error": str(e)}), 500

def format_stock_value(value, is_price=False, is_percent=False, is_volume=False):
    """
    Formate les valeurs des actions avec gestion des valeurs manquantes
    """
    if value is None or value == '':
        return "N/A"
    if value == 0 and not is_volume:  # Les volumes peuvent être 0
        return "N/A"
    if is_price:
        return round(float(value), 2)
    if is_percent:
        return round(float(value), 2)
    if is_volume:
        return int(value) if value > 0 else "N/A"
    return value

def get_live_exchange_rate(from_currency: str, to_currency: str = 'CHF') -> float:
    """
    Récupère le taux de change en direct en utilisant l'API FreeCurrency.
    Convertit une valeur de 'from_currency' vers 'to_currency'.
    """
    if from_currency == to_currency:
        return 1.0
    
    now = time.time()
    cache_key = f"forex_{from_currency}_{to_currency}"

    # 1. Vérifier si le taux est en cache et valide
    if cache_key in forex_cache and now - forex_cache[cache_key]['timestamp'] < FOREX_CACHE_DURATION:
        return forex_cache[cache_key]['rate']

    # 2. Appel API FreeCurrency
    logger.info(f"💰 Appel API FreeCurrency pour {from_currency} -> {to_currency}")
    try:
        import requests
        url = f"https://api.freecurrencyapi.com/v1/latest?apikey={FREECURRENCY_API_KEY}&currencies={to_currency}&base_currency={from_currency}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rate = data.get('data', {}).get(to_currency)
        if rate:
            # Mettre à jour le cache
            forex_cache[cache_key] = {'rate': rate, 'timestamp': now}
            return rate
        else:
            logger.warning(f"Taux de change non trouvé pour {from_currency} -> {to_currency}")
            return 1.0
            
    except Exception as e:
        logger.error(f"Erreur API FreeCurrency: {e}. Utilisation d'un taux de 1.0")
        return 1.0


@app.route("/api/exchange-rate/<from_currency>/<to_currency>")
def get_exchange_rate_route(from_currency: str, to_currency: str = 'CHF'):
    """Route pour récupérer le taux de change"""
    try:
        rate = get_live_exchange_rate(from_currency.upper(), to_currency.upper())
        return jsonify({
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "rate": rate,
            "last_update": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur taux de change: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stock-price/<symbol>")
def get_stock_price(symbol):
    """
    Récupère le prix actuel d'une action, avec Yahoo Finance en priorité
    et EODHD/Finnhub comme alternatives robustes.
    """
    # Vérifier si on force le refresh (ignore le cache)
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    items = AdvancedDataManager.fetch_all_items()
    item = next((i for i in items if i.stock_symbol == symbol), None)

    if not item:
        logger.warning(f"Aucun item trouvé pour le symbole {symbol}. L'API pourrait utiliser des hypothèses par défaut.")

    # Formater le symbole correctement selon la bourse
    formatted_symbol = symbol
    if item and item.stock_exchange and item.stock_exchange.upper() in ['SWX', 'SIX', 'SWISS', 'CH']:
        # Pour les actions suisses, s'assurer d'avoir le suffixe .SW
        if not symbol.endswith('.SW'):
            formatted_symbol = f"{symbol}.SW"
            logger.info(f"Formatage du symbole suisse: {symbol} -> {formatted_symbol}")

    cache_key = f"stock_price_{symbol}"
    
    # Si on ne force pas le refresh, vérifier le cache
    if not force_refresh and cache_key in stock_price_cache:
        cached_data = stock_price_cache[cache_key]
        
        if time.time() - cached_data['timestamp'] < STOCK_PRICE_CACHE_DURATION:
            logger.info(f"Prix depuis le cache pour {symbol}")
            return jsonify(cached_data['data'])
    
    # Si on force le refresh, logger l'action
    if force_refresh:
        logger.info(f"Refresh forcé pour {symbol} - cache ignoré")

    try:
        # Exclure IREN de Yahoo Finance (cause des erreurs 429)
        if symbol.upper() == 'IREN' or symbol.upper() == 'IREN.SW':
            logger.info(f"IREN exclu de Yahoo Finance, bascule direct sur EODHD")
            return get_stock_price_eodhd(formatted_symbol, item, cache_key, force_refresh)
        
        import yfinance as yf
        # Délai plus long pour éviter rate limiting Yahoo Finance
        time.sleep(3)
        ticker = yf.Ticker(formatted_symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not current_price:
             hist = ticker.history(period="1d")
             if not hist.empty:
                 current_price = hist['Close'].iloc[-1]

        if not current_price:
            raise Exception("Prix non trouvé sur Yahoo Finance, essai avec EODHD")

        # Récupérer les variations depuis Yahoo Finance
        previous_close = info.get('previousClose', 0)
        change = 0
        change_percent = 0
        
        if previous_close and current_price:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close > 0 else 0
        else:
            # Essayer de récupérer depuis les champs Yahoo Finance
            change = info.get('regularMarketChange', 0)
            change_percent = info.get('regularMarketChangePercent', 0)

        currency = info.get('currency', 'USD')
        # Pour les cartes, on garde le prix dans la devise originale
        # La conversion CHF sera utilisée uniquement pour le dashboard total
        price_chf = current_price

        # Récupérer les données historiques pour 52W plus précises
        try:
            hist = ticker.history(period="1y")
            if not hist.empty:
                actual_52w_high = hist['High'].max()
                actual_52w_low = hist['Low'].min()
                # Utiliser les données historiques si elles sont plus précises
                yahoo_52w_high = info.get('fiftyTwoWeekHigh')
                yahoo_52w_low = info.get('fiftyTwoWeekLow')
                
                # Comparer et choisir la meilleure valeur
                if yahoo_52w_high and abs(actual_52w_high - yahoo_52w_high) < 1:
                    final_52w_high = yahoo_52w_high
                else:
                    final_52w_high = actual_52w_high
                    
                if yahoo_52w_low and abs(actual_52w_low - yahoo_52w_low) < 1:
                    final_52w_low = yahoo_52w_low
                else:
                    final_52w_low = actual_52w_low
            else:
                final_52w_high = info.get('fiftyTwoWeekHigh')
                final_52w_low = info.get('fiftyTwoWeekLow')
        except:
            final_52w_high = info.get('fiftyTwoWeekHigh')
            final_52w_low = info.get('fiftyTwoWeekLow')

        result = {
            "symbol": symbol,
            "price": current_price,
            "price_chf": price_chf,
            "currency": currency,
            "company_name": info.get('longName', symbol),
            "last_update": datetime.now().isoformat(),
            "source": "Yahoo Finance (Taux de change via Finnhub)",
            "change": format_stock_value(change, is_price=True),
            "change_percent": format_stock_value(change_percent, is_percent=True),
            "volume": format_stock_value(info.get('volume'), is_volume=True),
            "average_volume": format_stock_value(info.get('averageVolume'), is_volume=True),
            "pe_ratio": format_stock_value(info.get('trailingPE'), is_price=True),
            "fifty_two_week_high": format_stock_value(final_52w_high, is_price=True),
            "fifty_two_week_low": format_stock_value(final_52w_low, is_price=True)
        }
        
        # Toujours mettre à jour le cache, même en cas de refresh forcé
        stock_price_cache[cache_key] = {'data': result, 'timestamp': time.time()}
        return jsonify(result)

    except Exception as e:
        if "429" in str(e) or "rate limit" in str(e).lower():
            logger.warning(f"Rate limit Yahoo Finance pour {symbol}, utilisation du cache")
            if cache_key in stock_price_cache:
                logger.info(f"Retour des données en cache pour {symbol}")
                return jsonify(stock_price_cache[cache_key]['data'])
        
        logger.warning(f"Yahoo Finance a échoué pour {symbol} ({e}), bascule sur EODHD.")
        
        # Essayer EODHD comme fallback
        logger.info(f"Essai avec EODHD pour {formatted_symbol}")
        return get_stock_price_eodhd(formatted_symbol, item, cache_key, force_refresh)


@app.route("/api/stock-price/cache/clear", methods=["POST"])
def clear_stock_price_cache():
    """
    Vide complètement le cache des prix des actions
    """
    try:
        global stock_price_cache
        cache_size = len(stock_price_cache)
        stock_price_cache.clear()
        logger.info(f"Cache des prix des actions vidé ({cache_size} entrées supprimées)")
        return jsonify({
            "success": True,
            "message": f"Cache vidé avec succès ({cache_size} entrées supprimées)",
            "cache_size_before": cache_size,
            "cache_size_after": 0
        })
    except Exception as e:
        logger.error(f"Erreur lors du vidage du cache: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/stock-price/cache/status")
def get_stock_price_cache_status():
    """
    Retourne le statut du cache des prix des actions
    """
    try:
        cache_size = len(stock_price_cache)
        cache_keys = list(stock_price_cache.keys())
        
        # Calculer l'âge des entrées en cache
        current_time = time.time()
        cache_ages = {}
        expired_entries = 0
        
        for key, data in stock_price_cache.items():
            age = current_time - data['timestamp']
            cache_ages[key] = age
            if age > STOCK_PRICE_CACHE_DURATION:
                expired_entries += 1
        
        return jsonify({
            "cache_size": cache_size,
            "cache_duration": STOCK_PRICE_CACHE_DURATION,
            "expired_entries": expired_entries,
            "cache_keys": cache_keys,
            "cache_ages": cache_ages,
            "eodhd_quota_warning": "⚠️ Quota EODHD probablement dépassé (20 req/jour). Utilisez les prix manuels."
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut du cache: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route("/api/eodhd/quota")
def check_eodhd_quota():
    """Vérifie le quota EODHD restant"""
    try:
        import requests
        # Test avec un symbole simple
        test_url = f"https://eodhd.com/api/real-time/AAPL?api_token={EODHD_API_KEY}&fmt=json"
        response = requests.get(test_url, timeout=5)
        
        if response.status_code == 402:
            return jsonify({
                "quota_exceeded": True,
                "message": "Quota EODHD dépassé (20 requêtes/jour)",
                "reset_time": "Minuit (heure locale)",
                "suggestion": "Utilisez les prix manuels ou attendez le reset"
            })
        elif response.status_code == 200:
            return jsonify({
                "quota_exceeded": False,
                "message": "Quota EODHD disponible",
                "remaining_requests": "Inconnu (API ne fournit pas cette info)"
            })
        else:
            return jsonify({
                "quota_exceeded": "Unknown",
                "status_code": response.status_code,
                "message": f"Statut inattendu: {response.status_code}"
            })
            
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Impossible de vérifier le quota"
        }), 500


@app.route("/api/stock-price/update-all", methods=["POST"])
def update_all_stock_prices():
    """Met à jour tous les prix d'actions dans la DB"""
    try:
        items = AdvancedDataManager.fetch_all_items()
        action_items = [item for item in items if item.category == 'Actions' and item.stock_symbol]
        
        if not action_items:
            return jsonify({
                "success": True,
                "message": "Aucune action trouvée à mettre à jour",
                "updated_count": 0
            })
        
        updated_count = 0
        errors = []
        
        for item in action_items:
            try:
                cache_key = f"stock_{item.stock_symbol}"
                # Forcer le refresh
                result = get_stock_price_eodhd(item.stock_symbol, item, cache_key, force_refresh=True)
                
                if hasattr(result, 'json'):
                    data = result.json
                    if isinstance(data, dict) and 'price' in data:
                        updated_count += 1
                        logger.info(f"✅ Prix mis à jour pour {item.name}: {data['price']} CHF")
                    else:
                        errors.append(f"Données invalides pour {item.name}")
                else:
                    errors.append(f"Réponse invalide pour {item.name}")
                    
            except Exception as e:
                error_msg = f"Erreur pour {item.name}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        return jsonify({
            "success": True,
            "message": f"Mise à jour terminée: {updated_count} actions mises à jour",
            "updated_count": updated_count,
            "total_actions": len(action_items),
            "errors": errors
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour globale: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def get_stock_price_eodhd(symbol: str, item: Optional[CollectionItem], cache_key: str, force_refresh=False):
    """
    Récupère le prix via l'API EODHD. Excellente pour les actions suisses.
    Limite: 20 requêtes par jour.
    """
    if not EODHD_API_KEY:
        return jsonify({"error": "Clé API EODHD non configurée"}), 500

    try:
        logger.info(f"Interrogation d'EODHD avec le symbole : {symbol}")
        
        import requests
        
        # Pour les actions suisses, essayer plusieurs variantes de symboles
        symbol_variants = [symbol]  # Commencer par le symbole fourni
        
        if item and item.stock_exchange and item.stock_exchange.upper() in ['SWX', 'SIX', 'SWISS', 'CH']:
            # Ajouter des variantes pour les actions suisses
            base_symbol = symbol.replace('.SW', '').replace('.SWX', '').replace('.SIX', '')
            symbol_variants.extend([
                f"{base_symbol}.SW",  # Format suisse standard
                f"{base_symbol}.SWX",  # Format SWX
                f"{base_symbol}.SIX",  # Format SIX
                base_symbol,  # Symbole sans suffixe
            ])
            # Supprimer les doublons
            symbol_variants = list(dict.fromkeys(symbol_variants))
        
        data = None
        working_symbol = symbol
        
        # Essayer chaque variante de symbole
        for variant in symbol_variants:
            logger.info(f"Essai EODHD avec le symbole: '{variant}'")
            quote_url = f"https://eodhd.com/api/real-time/{variant}?api_token={EODHD_API_KEY}&fmt=json"
            response = requests.get(quote_url, timeout=10)
            
            if response.status_code == 429:
                raise Exception("Rate limit EODHD atteint")
            
            if response.ok:
                response_data = response.json()
                if response_data and len(response_data) > 0:
                    data = response_data
                    working_symbol = variant
                    logger.info(f"✅ Symbole EODHD '{variant}' fonctionne")
                    break
            else:
                logger.warning(f"Symbole EODHD '{variant}' invalide (status: {response.status_code})")
        
        # Si aucune variante n'a fonctionné
        if not data or len(data) == 0:
            raise Exception(f"Aucune donnée trouvée pour les variantes de '{symbol}' sur EODHD")
        
        # EODHD retourne un array, prendre le premier élément
        quote = data[0] if isinstance(data, list) else data
        current_price = float(quote.get("close", 0))
        
        if current_price <= 0:
            raise Exception("Prix invalide reçu d'EODHD")
        
        # Récupérer la devise
        currency = quote.get("currency", "USD")
        # Pour les actions suisses, on suppose CHF
        if item and item.stock_exchange and item.stock_exchange.upper() in ['SWX', 'SIX', 'SWISS', 'CH']:
            currency = "CHF"
        
        # Pour les cartes, on garde le prix dans la devise originale
        price_chf = current_price
        
        # Récupérer les données fondamentales pour le PE ratio
        pe_ratio = "N/A"
        try:
            fundamental_url = f"https://eodhd.com/api/fundamentals/{working_symbol}?api_token={EODHD_API_KEY}&fmt=json"
            fundamental_response = requests.get(fundamental_url, timeout=10)
            
            if fundamental_response.ok:
                fundamental_data = fundamental_response.json()
                if fundamental_data and 'General' in fundamental_data:
                    general_data = fundamental_data['General']
                    if 'PERatio' in general_data and general_data['PERatio']:
                        pe_ratio = str(general_data['PERatio'])
                    logger.info(f"✅ Données fondamentales EODHD récupérées pour {working_symbol}")
        except Exception as e:
            logger.warning(f"Impossible de récupérer les données fondamentales EODHD pour {working_symbol}: {e}")
        
        result = {
            "symbol": symbol,  # Garder le symbole original pour l'affichage
            "price": current_price,
            "price_chf": price_chf,
            "currency": currency,
            "company_name": quote.get("code", symbol),
            "last_update": datetime.now().isoformat(),
            "source": f"EODHD (symbole utilisé: {working_symbol})",
            "change": format_stock_value(quote.get("change"), is_price=True),
            "change_percent": format_stock_value(quote.get("change_p"), is_percent=True),
            "volume": format_stock_value(quote.get("volume"), is_volume=True),
            "average_volume": format_stock_value(quote.get("avg_volume"), is_volume=True),
            "pe_ratio": pe_ratio,
            "fifty_two_week_high": format_stock_value(quote.get("high_52_weeks"), is_price=True),
            "fifty_two_week_low": format_stock_value(quote.get("low_52_weeks"), is_price=True)
        }
        
        logger.info(f"✅ Prix EODHD récupéré pour {symbol}: {current_price} {currency}")
        
        # Mettre en cache
        stock_price_cache[cache_key] = {'data': result, 'timestamp': time.time()}
        
        # Mettre à jour le prix dans la DB si c'est une action existante
        if item and item.id:
            try:
                update_data = {
                    'current_price': current_price,
                    'last_price_update': datetime.now().isoformat(),
                    'stock_volume': quote.get("volume"),
                    'stock_pe_ratio': pe_ratio if pe_ratio != "N/A" else None,
                    'stock_52_week_high': quote.get("high_52_weeks"),
                    'stock_52_week_low': quote.get("low_52_weeks"),
                    'stock_change': quote.get("change"),
                    'stock_change_percent': quote.get("change_p"),
                    'stock_average_volume': quote.get("avg_volume")
                }
                
                # Mettre à jour dans Supabase
                if supabase:
                    response = supabase.table('items').update(update_data).eq('id', item.id).execute()
                    if response.data:
                        logger.info(f"✅ Prix et métriques mis à jour dans DB pour action {item.name} (ID: {item.id}): {current_price} CHF")
                        logger.info(f"📊 Métriques: Volume={update_data['stock_volume']}, PE={update_data['stock_pe_ratio']}, 52W-H={update_data['stock_52_week_high']}, 52W-L={update_data['stock_52_week_low']}")
                    else:
                        logger.warning(f"⚠️ Échec mise à jour DB pour action {item.name} (ID: {item.id})")
            except Exception as e:
                logger.error(f"❌ Erreur mise à jour DB pour action {item.name}: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur EODHD pour {symbol}: {e}")
        
        # Utiliser le cache si disponible
        if cache_key in stock_price_cache:
            logger.info(f"Erreur API, retour des données en cache pour {symbol}")
            return jsonify(stock_price_cache[cache_key]['data'])
        
        return jsonify({
            "error": "Prix non disponible via EODHD", 
            "details": str(e),
            "message": "Veuillez mettre à jour le prix manuellement."
        }), 500


@app.route("/api/market-price/<int:item_id>")
def market_price(item_id):
    """Estimation de prix via IA avec 3 objets similaires"""
    if not openai_client:
        return jsonify({"error": "Moteur IA Indisponible"}), 503
    
    try:
        items = AdvancedDataManager.fetch_all_items()
        target_item = next((item for item in items if item.id == item_id), None)
        
        if not target_item:
            return jsonify({"error": "Objet non trouvé"}), 404
        
        # Analyse de marché avec objets similaires
        similar_items = [i for i in items if i.category == target_item.category and i.id != item_id]
        comparable_prices = [i.sold_price or i.asking_price for i in similar_items if i.sold_price or i.asking_price]
        
        # Tri des objets similaires par pertinence
        similar_items_with_prices = [
            i for i in similar_items 
            if (i.sold_price or i.asking_price) and i.construction_year
        ]
        
        # Calcul de score de similarité basé sur l'année et la catégorie
        def similarity_score(item):
            score = 100
            if target_item.construction_year and item.construction_year:
                year_diff = abs(target_item.construction_year - item.construction_year)
                score -= year_diff * 2  # Pénalité de 2 points par année d'écart
            return score
        
        # Tri par score de similarité
        similar_items_sorted = sorted(similar_items_with_prices, key=similarity_score, reverse=True)
        top_3_similar = similar_items_sorted[:3]
        
        market_context = ""
        if comparable_prices:
            avg_price = sum(comparable_prices) / len(comparable_prices)
            market_context = f"Prix moyen catégorie: {avg_price:,.0f} CHF (sur {len(comparable_prices)} objets)"
        
        # Contexte des 3 objets similaires
        similar_context = ""
        if top_3_similar:
            similar_context = "\n\nOBJETS SIMILAIRES DANS LA COLLECTION:"
            for i, similar_item in enumerate(top_3_similar, 1):
                price = similar_item.sold_price or similar_item.asking_price
                status = "Vendu" if similar_item.sold_price else "Prix demandé"
                similar_context += f"\n{i}. {similar_item.name} ({similar_item.construction_year or 'N/A'}) - {status}: {price:,.0f} CHF"
                if similar_item.description:
                    similar_context += f" - {similar_item.description[:80]}..."
        
        # Prompt adapté selon la catégorie
        if target_item.category == 'Actions':
            prompt = f"""Estime la valeur actuelle de cette position boursière en CHF :

POSITION À ÉVALUER:
- Nom: {target_item.name}
- Symbole: {target_item.stock_symbol or 'N/A'}
- Quantité: {target_item.stock_quantity or 1} actions
- Bourse: {target_item.stock_exchange or 'Non spécifiée'}
- Prix d'achat unitaire: {target_item.stock_purchase_price or 'N/A'} CHF
- Prix actuel connu: {target_item.current_price or 'N/A'} CHF/action
- Description: {target_item.description or 'N/A'}

INSTRUCTIONS:
1. Si un prix actuel est fourni, utilise-le pour calculer la valeur totale
2. Sinon, recherche le cours actuel de l'action {target_item.stock_symbol}
3. Calcule la valeur totale de la position (cours actuel × quantité)
4. Compare avec le prix d'achat pour calculer la plus/moins-value
5. Analyse les perspectives du titre

Réponds en JSON avec:
- estimated_price (valeur totale actuelle de la position en CHF)
- reasoning (analyse détaillée)
- comparable_items (3 actions similaires du marché)
- confidence_score (0.1-0.9)
- market_trend (hausse/stable/baisse)"""
        else:
            prompt = f"""Estime le prix de marché actuel de cet objet en CHF en te basant sur le marché réel :

OBJET À ÉVALUER:
- Nom: {target_item.name}
- Catégorie: {target_item.category}
- Année: {target_item.construction_year or 'N/A'}
- État: {target_item.condition or 'N/A'}
- Description: {target_item.description or 'N/A'}

INSTRUCTIONS IMPORTANTES:
1. Recherche les prix actuels du marché pour ce modèle exact ou des modèles très similaires
2. Utilise tes connaissances du marché automobile/horloger/immobilier actuel
3. Compare avec des ventes récentes d'objets similaires sur le marché (pas dans ma collection)
4. Prends en compte l'année, l'état et les spécificités du modèle

Pour les voitures : considère les sites comme AutoScout24, Comparis, annonces spécialisées
Pour les montres : marché des montres d'occasion, chrono24, enchères récentes
Pour l'immobilier : prix au m² dans la région, transactions récentes

Réponds en JSON avec:
- estimated_price (nombre en CHF basé sur le marché actuel)
- reasoning (explication détaillée en français avec références de marché)
- comparable_items (array avec EXACTEMENT 3 objets comparables du MARCHÉ EXTERNE avec:
  - name: nom exact du modèle comparable
  - year: année
  - price: prix de marché actuel ou de vente récente
  - source: source de l'information (ex: "AutoScout24", "Vente aux enchères Christie's", "Marché suisse de l'occasion")
  - comparison_reason: pourquoi cet objet est comparable
)
- confidence_score (0.1-0.9)
- market_trend (hausse/stable/baisse)
- price_range (objet avec min et max basés sur le marché)"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Tu es un expert en évaluation d'objets de luxe et d'actifs financiers avec une connaissance approfondie du marché. Réponds en JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=800,
            timeout=20
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Enrichir avec les données de marché réelles
        result['market_analysis'] = {
            'comparable_items_count': len(similar_items),
            'average_category_price': sum(comparable_prices) / len(comparable_prices) if comparable_prices else 0,
            'price_range_market': [min(comparable_prices), max(comparable_prices)] if comparable_prices else [0, 0],
            'top_3_similar_actual': [
                {
                    'name': item.name,
                    'year': item.construction_year,
                    'price': item.sold_price or item.asking_price,
                    'status': 'sold' if item.sold_price else 'asking'
                }
                for item in top_3_similar
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur market_price: {e}")
        return jsonify({"error": "Moteur IA Indisponible"}), 500

@app.route("/api/chatbot", methods=["POST"])
def chatbot():
    """Chatbot utilisant OpenAI GPT-4 avec recherche sémantique RAG"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données requises"}), 400
        
        query = data.get("message", "").strip()
        if not query:
            return jsonify({"error": "Message requis"}), 400
        
        # Récupération des données
        items = AdvancedDataManager.fetch_all_items()
        analytics = AdvancedDataManager.calculate_advanced_analytics(items)
        
        logger.info(f"🎯 Requête: '{query}'")
        
        if ai_engine:
            # Génération de réponse via OpenAI avec RAG
            response = ai_engine.generate_response(query, items, analytics)
            
            # Détecter si la recherche sémantique a été utilisée
            search_type = "semantic" if "🔍 **Recherche intelligente activée**" in response else "standard"
            
            return jsonify({
                "reply": response,
                "metadata": {
                    "items_analyzed": len(items),
                    "ai_engine": "openai_gpt4_with_rag",
                    "mode": "pure_with_semantic_search",
                    "search_type": search_type,
                    "embeddings_available": sum(1 for item in items if item.embedding),
                    "stocks_count": len([i for i in items if i.category == "Actions"])
                }
            })
        else:
            return jsonify({
                "reply": "❌ Moteur IA Indisponible",
                "metadata": {
                    "ai_engine": "unavailable"
                }
            })
        
    except Exception as e:
        logger.error(f"Erreur chatbot: {e}")
        return jsonify({
            "reply": "❌ Moteur IA Indisponible",
            "error": str(e)
        }), 500

@app.route("/api/embeddings/generate", methods=["POST"])
def generate_embeddings():
    """Génère les embeddings pour tous les objets qui n'en ont pas"""
    if not ai_engine or not ai_engine.semantic_search:
        return jsonify({"error": "Moteur de recherche sémantique non disponible"}), 503
    
    try:
        items = AdvancedDataManager.fetch_all_items()
        items_without_embedding = [item for item in items if not item.embedding]
        
        if not items_without_embedding:
            return jsonify({
                "message": "Tous les objets ont déjà un embedding",
                "total_items": len(items),
                "items_with_embedding": len(items)
            })
        
        success_count = 0
        errors = []
        
        for item in items_without_embedding:
            try:
                # Générer l'embedding
                embedding = ai_engine.semantic_search.generate_embedding_for_item(item)
                
                if embedding:
                    # Sauvegarder dans Supabase
                    supabase.table("items").update({"embedding": embedding}).eq("id", item.id).execute()
                    success_count += 1
                    logger.info(f"✅ Embedding généré pour: {item.name}")
                else:
                    errors.append(f"Échec génération pour: {item.name}")
                    
            except Exception as e:
                errors.append(f"Erreur pour {item.name}: {str(e)}")
                logger.error(f"Erreur génération embedding: {e}")
        
        # Invalider le cache
        smart_cache.invalidate('items')
        
        return jsonify({
            "message": f"Génération d'embeddings terminée",
            "total_processed": len(items_without_embedding),
            "success": success_count,
            "errors": len(errors),
            "error_details": errors[:10]  # Limiter les détails d'erreur
        })
        
    except Exception as e:
        logger.error(f"Erreur génération embeddings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/test-email", methods=["POST"])
def test_email():
    """Route pour tester les notifications Gmail"""
    try:
        data = request.get_json() or {}
        test_type = data.get('type', 'general')
        
        if test_type == 'sale_status':
            # Test changement de statut
            gmail_manager.notify_sale_status_change(
                {
                    'name': 'Test Lamborghini Aventador',
                    'category': 'Voitures',
                    'asking_price': 500000,
                    'construction_year': 2023,
                    'for_sale': True,
                    'sale_progress': 'Négociation avancée avec 2 acheteurs sérieux. Visites programmées cette semaine.'
                },
                'inquiries',
                'negotiation'
            )
            message = "Email de test envoyé: changement de statut de vente"
            
        elif test_type == 'new_offer':
            # Test nouvelle offre
            gmail_manager.notify_new_offer(
                {
                    'name': 'Test Ferrari 488 GTB',
                    'category': 'Voitures',
                    'asking_price': 300000,
                    'construction_year': 2022,
                    'for_sale': True,
                    'description': 'Ferrari 488 GTB en parfait état, entretien complet, historique certifié.'
                },
                270000
            )
            message = "Email de test envoyé: nouvelle offre"
            
        else:
            # Test général
            gmail_manager.notify_item_created({
                'name': 'Test Patek Philippe Nautilus',
                'category': 'Montres',
                'for_sale': False,
                'asking_price': 180000,
                'construction_year': 2022,
                'status': 'Available'
            })
            message = "Email de test envoyé: nouvel objet"
        
        return jsonify({
            "success": True,
            "message": message,
            "email_enabled": gmail_manager.enabled,
            "recipients": gmail_manager.recipients
        })
        
    except Exception as e:
        logger.error(f"Erreur test email: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/email-config")
def email_config():
    """Retourne la configuration Gmail"""
    return jsonify({
        "enabled": gmail_manager.enabled,
        "recipients": gmail_manager.recipients,
        "recipients_count": len(gmail_manager.recipients),
        "host": gmail_manager.email_host,
        "port": gmail_manager.email_port,
        "user_configured": bool(gmail_manager.email_user),
        "service": "Gmail",
        "app_url": APP_URL
    })

@app.route("/api/endpoints")
def list_endpoints():
    """Liste tous les endpoints disponibles"""
    endpoints = []
    for rule in app.url_map.iter_rules():
        endpoints.append({
            "endpoint": rule.rule,
            "methods": list(rule.methods - {'HEAD', 'OPTIONS'})
        })
    
    return jsonify({
        "available_endpoints": sorted(endpoints, key=lambda x: x['endpoint']),
        "total_count": len(endpoints),
        "chatbot_endpoint": "/api/chatbot",
        "ai_mode": "openai_gpt4_with_semantic_rag",
        "app_url": APP_URL,
        "new_features": [
            "Recherche sémantique RAG",
            "Génération automatique d'embeddings",
            "Recherche intelligente par similarité",
            "Détection d'intention de requête",
            "Support complet des actions boursières",
            "Mise à jour automatique des prix avec gestion 429",
            "Prix manuel pour les actions",
            "Génération PDF pixel perfect"
        ]
    })

@app.route("/api/portfolio/pdf", methods=["GET"])
def generate_portfolio_pdf():
    """Génère un PDF pixel perfect du portefeuille complet"""
    try:
        # Récupérer tous les items
        items = AdvancedDataManager.fetch_all_items()
        
        # Calculer les statistiques
        total_items = len(items)
        available_items = len([item for item in items if item.status == 'Available'])
        categories = set([item.category for item in items if item.category])
        categories_count = len(categories)
        
        # Calculer la valeur totale
        total_value = 0
        for item in items:
            if item.status == 'Sold':
                continue
            if item.category == 'Actions' and item.current_price and item.stock_quantity:
                total_value += item.current_price * item.stock_quantity
            elif item.status == 'Available' and item.asking_price:
                total_value += item.asking_price
        
        # Organiser les données par catégorie
        categories_data = {}
        actions = []
        
        for item in items:
            if item.category == 'Actions':
                actions.append(item)
            else:
                if item.category not in categories_data:
                    categories_data[item.category] = []
                categories_data[item.category].append(item)
        
        # Fonction pour formater les prix
        def format_price(price):
            if not price or price == 0:
                return '0 CHF'
            try:
                return f"{price:,.0f} CHF"
            except:
                return '0 CHF'
        
        # Préparer les données pour le template
        template_data = {
            'generation_date': datetime.now().strftime('%d/%m/%Y à %H:%M'),
            'total_items': total_items,
            'total_value': format_price(total_value),
            'available_items': available_items,
            'categories_count': categories_count,
            'actions': actions,
            'categories': categories_data
        }
        
        # Rendre le template HTML
        html_content = render_template('portfolio_pdf.html', **template_data)
        
        # Générer le PDF avec WeasyPrint
        try:
            from weasyprint import HTML
            from weasyprint.text.fonts import FontConfiguration
            
            # Configuration des polices
            font_config = FontConfiguration()
            
            # Créer le PDF
            pdf = HTML(string=html_content).write_pdf(
                font_config=font_config
            )
            
            # Retourner le PDF
            from flask import Response
            response = Response(pdf, mimetype='application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename=bonvin_portfolio_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
            
            logger.info(f"✅ PDF généré avec succès: {total_items} items, {categories_count} catégories")
            return response
            
        except ImportError:
            logger.error("❌ WeasyPrint non installé")
            return jsonify({
                "error": "WeasyPrint non installé. Installez avec: pip install weasyprint"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Erreur génération PDF: {e}")
        return jsonify({
            "error": str(e)
        }), 500

# Fonctions utilitaires
def clean_update_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Nettoie les données de mise à jour - CORRIGÉ POUR INCLURE LES ACTIONS"""
    cleaned = {}
    
    # Champs texte (INCLUT LES CHAMPS ACTIONS)
    text_fields = [
        'name', 'category', 'description', 'sale_progress', 
        'buyer_contact', 'intermediary', 'status', 'condition', 
        'sale_status', 'stock_symbol', 'stock_exchange'
    ]
    for field in text_fields:
        if field in data:
            cleaned[field] = data[field].strip() if data[field] else None
    
    # Champs numériques (INCLUT stock_purchase_price et current_price)
    numeric_fields = [
        'asking_price', 'sold_price', 'acquisition_price', 
        'current_offer', 'commission_rate', 'surface_m2', 
        'rental_income_chf', 'stock_purchase_price', 'current_price',
        'stock_pe_ratio', 'stock_52_week_high', 'stock_52_week_low',
        'stock_change', 'stock_change_percent'
    ]
    for field in numeric_fields:
        if field in data:
            try:
                cleaned[field] = float(data[field]) if data[field] else None
            except:
                cleaned[field] = None
    
    # Champs entiers
    if 'construction_year' in data:
        try:
            cleaned['construction_year'] = int(data['construction_year']) if data['construction_year'] else None
        except:
            cleaned['construction_year'] = None
    
    if 'stock_quantity' in data:
        try:
            cleaned['stock_quantity'] = int(data['stock_quantity']) if data['stock_quantity'] else None
        except:
            cleaned['stock_quantity'] = None
    
    # Champs entiers pour les métriques boursières
    volume_fields = ['stock_volume', 'stock_average_volume']
    for field in volume_fields:
        if field in data:
            try:
                cleaned[field] = int(data[field]) if data[field] else None
            except:
                cleaned[field] = None
    
    # Booléen
    if 'for_sale' in data:
        cleaned['for_sale'] = bool(data['for_sale'])
    
    if 'last_action_date' in data:
        cleaned['last_action_date'] = data['last_action_date']
    
    # Logique métier : nettoyer les champs actions si pas une action
    # MAIS préserver le current_price si il existe déjà
    if cleaned.get('category') != 'Actions':
        cleaned['stock_symbol'] = None
        cleaned['stock_quantity'] = None
        cleaned['stock_purchase_price'] = None
        cleaned['stock_exchange'] = None
        # NE PAS effacer current_price ici - il peut être mis à jour manuellement
    
    # Logique métier existante pour les ventes
    if cleaned.get('for_sale') == False:
        cleaned['sale_status'] = 'initial'
        cleaned['sale_progress'] = None
        cleaned['buyer_contact'] = None
        cleaned['intermediary'] = None
        cleaned['current_offer'] = None
        cleaned['commission_rate'] = None
        cleaned['last_action_date'] = None
    
    return cleaned

# Gestion d'erreurs
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Page non trouvée"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Erreur interne du serveur"}), 500

# Point d'entrée
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = "0.0.0.0"
    
    logger.info("=" * 60)
    logger.info("🚀 BONVIN COLLECTION - VERSION OPENAI AVEC RAG")
    logger.info("=" * 60)
    logger.info(f"🌐 Host: {host}:{port}")
    logger.info(f"🔗 App URL: {APP_URL}")
    logger.info(f"🗄️ Supabase: {'✅' if supabase else '❌'}")
    logger.info(f"🤖 OpenAI: {'✅' if openai_client else '❌'}")
    logger.info(f"🧠 IA Engine: {'✅ GPT-4 avec RAG' if ai_engine else '❌'}")
    logger.info(f"📧 Gmail: {'✅' if gmail_manager.enabled else '❌'}")
    if gmail_manager.enabled:
        logger.info(f"📬 Destinataires: {len(gmail_manager.recipients)}")
    logger.info(f"💾 Cache: ✅ Multi-niveaux avec embeddings")
    logger.info(f"📈 Support Actions: ✅ Complet avec prix temps réel")
    logger.info("=" * 60)
    logger.info("MODE: OpenAI Pure avec Recherche Sémantique RAG")
    logger.info("✅ GPT-4 avec recherche intelligente")
    logger.info("✅ Embeddings OpenAI text-embedding-3-small")
    logger.info("✅ Recherche sémantique par similarité cosinus")
    logger.info("✅ Détection d'intention de requête")
    logger.info("✅ Génération automatique d'embeddings")
    logger.info("✅ Cache intelligent pour les embeddings")
    logger.info("✅ Support complet des actions boursières")
    logger.info("✅ Gestion des erreurs 429 avec cache")
    logger.info("✅ Prix manuel pour les actions")
    logger.info("=" * 60)
    
    try:
        app.run(debug=False, host=host, port=port)
    except Exception as e:
        logger.error(f"❌ Erreur démarrage: {e}")
        raise
