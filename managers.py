"""
Classes de gestionnaires pour l'application Inventory SBO
"""
import os
import sqlite3
import smtplib
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


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


class ConversationMemoryStore:
    """SQLite-backed memory store for conversation history per session_id."""

    def __init__(self, db_filename: str = "chat_memory.db"):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            base_dir = os.getcwd()
        self.db_path = os.path.join(base_dir, db_filename)
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _ensure_schema(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            # Index for quick retrieval
            cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id)")
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO messages(session_id, role, content, created_at) VALUES (?,?,?,?)",
                    (session_id, role, content, datetime.utcnow().isoformat()),
                )
                conn.commit()
        except Exception:
            # Memory is best-effort; avoid breaking the request
            pass

    def get_recent_messages(self, session_id: str, limit: int = 12):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
                    (session_id, max(1, int(limit))),
                )
                rows = cur.fetchall()
                # Return in chronological order
                return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
        except Exception:
            return []


class GmailNotificationManager:
    """Gestionnaire des notifications Gmail avancé avec templates HTML"""
    
    def __init__(self):
        self.email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.email_port = int(os.getenv("EMAIL_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_recipients = [r.strip() for r in os.getenv("EMAIL_RECIPIENTS", "").split(",") if r.strip()]
        
        if not self.email_user or not self.email_password:
            logger.warning("⚠️ Configuration email incomplète")
        if not self.email_recipients:
            logger.warning("⚠️ Aucun destinataire configuré")
    
    def send_collection_update_email(self, item_name: str, changes: List[str], old_data: Dict, new_data: Dict) -> bool:
        """Envoie un email de notification pour les mises à jour importantes"""
        if not self._is_configured():
            logger.warning("Email non configuré, notification ignorée")
            return False
        
        # Vérifier si c'est assez important pour envoyer un email
        if not self._is_important_change(changes):
            logger.info("Changement pas assez important pour un email")
            return False
        
        try:
            # Construire l'email avec template HTML
            subject = f"📦 Mise à jour importante: {item_name}"
            html_content = self._create_update_html(item_name, changes, old_data, new_data)
            text_content = self._create_update_text(item_name, changes)
            
            return self._send_email(subject, text_content, html_content)
            
        except Exception as e:
            logger.error(f"Erreur envoi email collection: {e}")
            return False
    
    def send_market_report_email(self, market_report_data: Dict) -> bool:
        """Envoie un email avec le rapport de marché"""
        if not self._is_configured():
            logger.warning("Email non configuré, rapport ignoré")
            return False
        
        try:
            report_date = market_report_data.get('date', 'Date inconnue')
            report_time = market_report_data.get('time', 'Heure inconnue')
            report_content = market_report_data.get('content', 'Contenu non disponible')
            
            subject = f"📊 Rapport de Marché - {report_date}"
            
            # Créer le contenu HTML et texte
            html_content = self._create_market_report_html(report_date, report_time, report_content)
            
            # Version texte simplifiée
            text_content = self._create_market_report_text(report_date, report_time, report_content)
            
            return self._send_email(subject, text_content, html_content)
            
        except Exception as e:
            logger.error(f"Erreur envoi email rapport marché: {e}")
            return False
    
    def _is_configured(self) -> bool:
        """Vérifie si l'email est correctement configuré"""
        return bool(self.email_user and self.email_password and self.email_recipients)
    
    def _is_important_change(self, changes: List[str]) -> bool:
        """Détermine si un changement mérite un email"""
        # Mots-clés pour changements importants
        important_keywords = [
            'vente', 'vendu', 'offre', 'négociation', 'prix', 'statut de vente',
            'mise en vente', 'retiré de la vente', 'finalisation'
        ]
        
        changes_text = ' '.join(changes).lower()
        return any(keyword in changes_text for keyword in important_keywords)
    
    def _send_email(self, subject: str, text_content: str, html_content: str = None) -> bool:
        """Envoie l'email avec gestion d'erreurs robuste"""
        if not self._is_configured():
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = ', '.join(self.email_recipients)
            
            # Ajouter le contenu texte
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Ajouter le contenu HTML si disponible
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Connexion et envoi avec retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with smtplib.SMTP(self.email_host, self.email_port) as server:
                        server.starttls()
                        server.login(self.email_user, self.email_password)
                        
                        for recipient in self.email_recipients:
                            server.send_message(msg, to_addrs=[recipient])
                        
                        logger.info(f"✅ Email envoyé avec succès: {subject}")
                        return True
                        
                except smtplib.SMTPException as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Tentative {attempt + 1} échouée, nouvelle tentative: {e}")
                        continue
                    else:
                        logger.error(f"Échec définitif envoi email après {max_retries} tentatives: {e}")
                        return False
                        
        except Exception as e:
            logger.error(f"Erreur critique envoi email: {e}")
            return False
    
    def _create_market_report_html(self, report_date: str, report_time: str, report_content: str) -> str:
        """Crée le contenu HTML pour le rapport de marché"""
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Rapport de Marché BONVIN</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #007bff;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .logo {{
                    width: 120px;
                    height: auto;
                    margin-bottom: 15px;
                }}
                h1 {{
                    color: #007bff;
                    margin: 0;
                    font-size: 28px;
                }}
                .subtitle {{
                    color: #6c757d;
                    font-style: italic;
                    margin-top: 5px;
                }}
                .report-info {{
                    background: #e9ecef;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 25px;
                }}
                .report-info h3 {{
                    margin-top: 0;
                    color: #495057;
                }}
                .report-content {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #007bff;
                }}
                .report-content h3 {{
                    margin-top: 0;
                    color: #007bff;
                }}
                pre {{
                    white-space: pre-wrap;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.4;
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #dee2e6;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="https://bonvin.ch/wp-content/uploads/2023/03/BONVIN_120x120.png" alt="BONVIN" class="logo">
                    <h1>📰 Rapport de Marché</h1>
                    <div class="subtitle">Analyse et insights des marchés financiers</div>
                </div>
                
                <div class="content">
                    <div class="report-info">
                        <h3>📋 Informations du Rapport</h3>
                        <p><strong>Date:</strong> {report_date}</p>
                        <p><strong>Heure:</strong> {report_time}</p>
                        <p><strong>Source:</strong> API Manus - Données temps réel</p>
                        <p><strong>Généré le:</strong> {timestamp}</p>
                    </div>
                    
                    <div class="report-content">
                        <h3>📊 Analyse de Marché</h3>
                        <pre>{report_content}</pre>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>BONVIN Collection</strong> - Gestion de portefeuille d'investissement</p>
                    <p>Ce rapport a été généré automatiquement par votre système de gestion</p>
                    <p>Pour plus d'informations, consultez votre tableau de bord</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_market_report_text(self, report_date: str, report_time: str, report_content: str) -> str:
        """Crée le contenu texte pour le rapport de marché"""
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        return f"""
BONVIN Collection - Rapport de Marché
====================================
📋 INFORMATIONS DU RAPPORT
Date: {report_date}
Heure: {report_time}
Source: API Manus - Données temps réel
Généré le: {timestamp}
📊 ANALYSE DE MARCHÉ
{report_content}

---
BONVIN Collection - Gestion de portefeuille d'investissement
Ce rapport a été généré automatiquement par votre système de gestion
        """
