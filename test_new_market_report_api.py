#!/usr/bin/env python3
"""
Test de la nouvelle API de rapport de marché Manus
"""

import sys
import os
import time
import logging
import requests

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_api_call():
    """Test direct de l'API de rapport de marché"""
    try:
        url = "https://5001-i6iozp7b45ajvx9qtfijb-2bff9589.manusvm.computer/api/report"
        
        logger.info("🧪 Test direct de l'API de rapport de marché")
        logger.info(f"📡 URL: {url}")
        
        headers = {
            'User-Agent': 'InventorySBO/1.0 (Test)'
        }
        
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=30)
        end_time = time.time()
        
        duration = end_time - start_time
        
        logger.info(f"⏱️ Durée de la requête: {duration:.2f}s")
        logger.info(f"📊 Status code: {response.status_code}")
        logger.info(f"📏 Taille de la réponse: {len(response.text)} caractères")
        
        if response.status_code == 200:
            content = response.text
            logger.info("✅ API accessible")
            
            # Analyser le contenu
            logger.info("📋 Analyse du contenu:")
            
            # Vérifier si c'est du HTML
            if '<html' in content.lower():
                logger.info("   ✅ Contenu HTML détecté")
                
                # Extraire le titre
                import re
                title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)
                if title_match:
                    logger.info(f"   📝 Titre: {title_match.group(1).strip()}")
                
                # Compter les balises
                h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
                h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
                p_count = len(re.findall(r'<p[^>]*>', content, re.IGNORECASE))
                
                logger.info(f"   📊 Structure: {h1_count} H1, {h2_count} H2, {p_count} P")
                
                # Afficher un extrait
                first_paragraph = re.search(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
                if first_paragraph:
                    text = re.sub(r'<[^>]+>', '', first_paragraph.group(1)).strip()
                    logger.info(f"   📄 Premier paragraphe: {text[:100]}...")
                
            else:
                logger.info("   ℹ️ Contenu non-HTML détecté")
                logger.info(f"   📄 Début du contenu: {content[:200]}...")
            
            return True
        else:
            logger.error(f"❌ Erreur HTTP {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test direct API: {e}")
        return False

def test_manus_integration():
    """Test de l'intégration avec manus_integration.py"""
    try:
        from manus_integration import ManusMarketReportAPI
        
        logger.info("🧪 Test intégration manus_integration.py")
        
        # Créer une instance
        api = ManusMarketReportAPI()
        
        # Test de récupération du rapport
        start_time = time.time()
        report = api.get_market_report(force_refresh=True)
        end_time = time.time()
        
        duration = end_time - start_time
        
        logger.info(f"⏱️ Durée de récupération: {duration:.2f}s")
        logger.info(f"📊 Status: {report.get('status', 'N/A')}")
        logger.info(f"📅 Date: {report.get('report_date', 'N/A')}")
        
        if report.get('status') == 'complete':
            logger.info("✅ Rapport récupéré avec succès")
            
            # Analyser le contenu
            content = report.get('content', {})
            logger.info(f"📄 Contenu HTML: {len(content.get('html', ''))} chars")
            logger.info(f"📝 Contenu Markdown: {len(content.get('markdown', ''))} chars")
            logger.info(f"📋 Contenu texte: {len(content.get('text', ''))} chars")
            
            # Afficher un extrait du markdown
            markdown = content.get('markdown', '')
            if markdown:
                lines = markdown.split('\n')[:5]
                logger.info("📄 Extrait du rapport:")
                for line in lines:
                    if line.strip():
                        logger.info(f"   {line}")
            
            # Analyser les métriques
            metrics = report.get('market_metrics', {})
            if metrics:
                logger.info(f"📊 Métriques extraites: {len(metrics)}")
                for key, value in list(metrics.items())[:5]:
                    logger.info(f"   {key}: {value}")
            
            return True
        else:
            logger.error(f"❌ Échec de récupération: {report.get('error', 'Erreur inconnue')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test intégration: {e}")
        return False

def test_app_integration():
    """Test de l'intégration avec app.py"""
    try:
        logger.info("🧪 Test intégration app.py")
        
        # Simuler l'appel comme dans app.py
        from manus_integration import get_market_report_manus
        
        start_time = time.time()
        report = get_market_report_manus(force_refresh=True)
        end_time = time.time()
        
        duration = end_time - start_time
        
        logger.info(f"⏱️ Durée via app.py: {duration:.2f}s")
        
        if report and report.get('status') == 'complete':
            logger.info("✅ Intégration app.py réussie")
            
            # Vérifier la structure attendue par app.py
            required_fields = ['timestamp', 'content', 'status']
            missing_fields = [field for field in required_fields if field not in report]
            
            if not missing_fields:
                logger.info("✅ Structure compatible avec app.py")
                return True
            else:
                logger.error(f"❌ Champs manquants: {missing_fields}")
                return False
        else:
            logger.error("❌ Échec intégration app.py")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur test app.py: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Début des tests de la nouvelle API de rapport de marché")
    
    # Test 1: Appel direct à l'API
    logger.info("\n" + "="*50)
    success1 = test_direct_api_call()
    
    # Test 2: Intégration manus_integration.py
    logger.info("\n" + "="*50)
    success2 = test_manus_integration()
    
    # Test 3: Intégration app.py
    logger.info("\n" + "="*50)
    success3 = test_app_integration()
    
    # Résumé
    logger.info("\n" + "="*50)
    logger.info("📋 RÉSUMÉ DES TESTS")
    logger.info(f"✅ Appel direct API: {'SUCCÈS' if success1 else 'ÉCHEC'}")
    logger.info(f"✅ Intégration manus_integration: {'SUCCÈS' if success2 else 'ÉCHEC'}")
    logger.info(f"✅ Intégration app.py: {'SUCCÈS' if success3 else 'ÉCHEC'}")
    
    if success1 and success2 and success3:
        logger.info("🎉 Tous les tests réussis!")
        logger.info("🚀 Nouvelle API de rapport de marché prête!")
        return True
    else:
        logger.error("❌ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 