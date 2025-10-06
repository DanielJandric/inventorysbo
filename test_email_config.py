#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration email
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_email_config():
    """Teste la configuration email en envoyant un email de test."""
    
    # Récupérer les variables d'environnement
    email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    email_port = int(os.getenv("EMAIL_PORT", "587"))
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    recipients = [e.strip() for e in os.getenv("EMAIL_RECIPIENTS", "").split(",") if e.strip()]
    
    logger.info("🔧 Test de la configuration email...")
    logger.info(f"   - Host: {email_host}")
    logger.info(f"   - Port: {email_port}")
    logger.info(f"   - User: {email_user}")
    logger.info(f"   - Password: {'*' * len(email_password) if email_password else 'Non défini'}")
    logger.info(f"   - Destinataires: {recipients}")
    
    # Vérifier que toutes les variables sont définies
    if not all([email_user, email_password, recipients]):
        logger.error("❌ Configuration email incomplète!")
        logger.error("   Assurez-vous que EMAIL_USER, EMAIL_PASSWORD et EMAIL_RECIPIENTS sont définis")
        return False
    
    try:
        # Créer un email de test
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = "[BONVIN] Test de Configuration Email"
        
        # Contenu HTML de test
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 3px solid #1e3a8a; padding-bottom: 20px; margin-bottom: 30px; }
                .header h1 { color: #1e3a8a; margin: 0; }
                .success { background: #dcfce7; padding: 20px; border-radius: 8px; border-left: 4px solid #22c55e; margin: 20px 0; }
                .info { background: #dbeafe; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Test de Configuration Email</h1>
                </div>
                
                <div class="success">
                    <h3>🎉 Configuration Email Réussie!</h3>
                    <p>Votre système est maintenant configuré pour envoyer automatiquement les rapports d'analyse de marché par email.</p>
                </div>
                
                <div class="info">
                    <h3>📧 Détails de la Configuration</h3>
                    <ul>
                        <li><strong>Serveur SMTP:</strong> {email_host}:{email_port}</li>
                        <li><strong>Compte:</strong> {email_user}</li>
                        <li><strong>Destinataires:</strong> {", ".join(recipients)}</li>
                    </ul>
                </div>
                
                <p>Le prochain rapport d'analyse de marché sera automatiquement envoyé par email à tous les destinataires configurés.</p>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #666; font-size: 12px;">
                    <p>Système BONVIN Collection - Test de Configuration</p>
                </div>
            </div>
        </body>
        </html>
        """.replace("{email_host}", str(email_host))\
           .replace("{email_port}", str(email_port))\
           .replace("{email_user}", str(email_user))\
           .replace("{recipients}", ", ".join(recipients))
        
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Tester la connexion SMTP
        logger.info("🔌 Test de connexion SMTP...")
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            logger.info("✅ Connexion TLS établie")
            
            # Test d'authentification
            logger.info("🔐 Test d'authentification...")
            server.login(email_user, email_password)
            logger.info("✅ Authentification réussie")
            
            # Envoi de l'email de test
            logger.info("📤 Envoi de l'email de test...")
            server.send_message(msg)
            logger.info("✅ Email de test envoyé avec succès!")
        
        logger.info("🎉 Configuration email validée avec succès!")
        logger.info(f"   - Email de test envoyé à {len(recipients)} destinataire(s)")
        logger.info("   - Vérifiez vos boîtes de réception (et spams)")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Erreur d'authentification: {e}")
        logger.error("   Vérifiez EMAIL_USER et EMAIL_PASSWORD")
        logger.error("   Pour Gmail, utilisez un mot de passe d'application")
        return False
        
    except smtplib.SMTPConnectError as e:
        logger.error(f"❌ Erreur de connexion: {e}")
        logger.error("   Vérifiez EMAIL_HOST et EMAIL_PORT")
        logger.error("   Assurez-vous que le serveur SMTP est accessible")
        return False
        
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {e}")
        return False

def main():
    """Fonction principale."""
    print("🚀 Test de Configuration Email - BONVIN Collection")
    print("=" * 60)
    
    success = test_email_config()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Configuration email validée avec succès!")
        print("   Votre système peut maintenant envoyer des rapports automatiquement.")
    else:
        print("❌ Configuration email échouée!")
        print("   Consultez le guide EMAIL_CONFIG.md pour la configuration.")
        print("   Vérifiez vos variables d'environnement dans Render.")

if __name__ == "__main__":
    main()
