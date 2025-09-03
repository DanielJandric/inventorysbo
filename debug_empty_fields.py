#!/usr/bin/env python3
"""
Script de diagnostic pour analyser pourquoi certains champs sont vides dans market_analyses
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_market_analyses():
    """Analyse les données de la table market_analyses"""
    try:
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        
        if not db.is_connected():
            logger.error("❌ Pas de connexion à la base de données")
            return
        
        # Récupérer les 10 dernières analyses
        analyses = db.get_recent_analyses(limit=10)
        
        if not analyses:
            logger.warning("⚠️ Aucune analyse trouvée")
            return
        
        logger.info(f"📊 Analyse de {len(analyses)} rapports récents")
        logger.info("=" * 60)
        
        for i, analysis in enumerate(analyses, 1):
            logger.info(f"\n📋 Rapport #{i} (ID: {analysis.id})")
            logger.info(f"   - Type: {analysis.analysis_type}")
            logger.info(f"   - Date: {analysis.timestamp}")
            logger.info(f"   - Statut: {analysis.worker_status}")
            
            # Analyser chaque champ
            fields_to_check = [
                ('executive_summary', analysis.executive_summary),
                ('summary', analysis.summary),
                ('key_points', analysis.key_points),
                ('insights', analysis.insights),
                ('risks', analysis.risks),
                ('opportunities', analysis.opportunities),
                ('sources', analysis.sources),
                ('structured_data', analysis.structured_data),
                ('geopolitical_analysis', analysis.geopolitical_analysis),
                ('economic_indicators', analysis.economic_indicators)
            ]
            
            for field_name, field_value in fields_to_check:
                if field_value is None:
                    logger.warning(f"   ❌ {field_name}: NULL")
                elif isinstance(field_value, list) and len(field_value) == 0:
                    logger.warning(f"   ⚠️ {field_name}: Liste vide")
                elif isinstance(field_value, dict) and len(field_value) == 0:
                    logger.warning(f"   ⚠️ {field_name}: Dictionnaire vide")
                elif isinstance(field_value, str) and len(field_value.strip()) == 0:
                    logger.warning(f"   ⚠️ {field_name}: String vide")
                else:
                    if isinstance(field_value, list):
                        logger.info(f"   ✅ {field_name}: {len(field_value)} éléments")
                    elif isinstance(field_value, dict):
                        logger.info(f"   ✅ {field_name}: {len(field_value)} clés")
                    else:
                        logger.info(f"   ✅ {field_name}: {len(str(field_value))} caractères")
            
            # Analyser le structured_data en détail
            if analysis.structured_data:
                logger.info(f"   🔍 Structured_data contient:")
                for key in analysis.structured_data.keys():
                    logger.info(f"      - {key}")
            
            logger.info("-" * 40)
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse: {e}")

def test_llm_response_format():
    """Test du format de réponse LLM attendu"""
    logger.info("\n🧪 Test du format de réponse LLM")
    logger.info("=" * 60)
    
    # Exemple de réponse LLM correcte
    correct_response = {
        "executive_summary": [
            "Point 1: Analyse des marchés",
            "Point 2: Focus sur l'IA",
            "Point 3: Tendance positive"
        ],
        "summary": "Résumé détaillé de l'analyse...",
        "key_points": [
            "Point clé 1",
            "Point clé 2",
            "Point clé 3"
        ],
        "insights": [
            "Insight 1: Observation importante",
            "Insight 2: Tendance émergente"
        ],
        "risks": [
            "Risque 1: Volatilité des marchés",
            "Risque 2: Tensions géopolitiques"
        ],
        "opportunities": [
            "Opportunité 1: Secteur technologique",
            "Opportunité 2: Marchés émergents"
        ],
        "sources": [
            {"title": "Source 1", "url": "http://example.com"}
        ],
        "confidence_score": 0.85
    }
    
    logger.info("✅ Format de réponse LLM correct:")
    for key, value in correct_response.items():
        if isinstance(value, list):
            logger.info(f"   - {key}: {len(value)} éléments")
        else:
            logger.info(f"   - {key}: {type(value).__name__}")
    
    # Exemple de réponse LLM problématique
    problematic_response = {
        "executive_summary": ["Point 1"],
        "summary": "Résumé court",
        "key_points": ["Point clé 1"],
        "insights": [],  # Liste vide
        "risks": [],     # Liste vide
        "opportunities": [],  # Liste vide
        "sources": [],
        "confidence_score": 0.5
    }
    
    logger.info("\n❌ Format de réponse LLM problématique:")
    for key, value in problematic_response.items():
        if isinstance(value, list) and len(value) == 0:
            logger.warning(f"   - {key}: LISTE VIDE")
        else:
            logger.info(f"   - {key}: {type(value).__name__}")

def check_prompt_requirements():
    """Vérifie les exigences du prompt LLM"""
    logger.info("\n📝 Vérification des exigences du prompt LLM")
    logger.info("=" * 60)
    
    # Lire le fichier scrapingbee_scraper.py pour extraire le prompt
    try:
        with open('scrapingbee_scraper.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher les mentions d'insights, risks, opportunities
        if 'insights' in content and 'risks' in content and 'opportunities' in content:
            logger.info("✅ Le prompt mentionne bien insights, risks, opportunities")
        else:
            logger.warning("⚠️ Le prompt ne mentionne pas tous les champs requis")
        
        # Chercher les exigences de format
        if 'FORMAT DE SORTIE CRITIQUE' in content:
            logger.info("✅ Le prompt contient des exigences de format strictes")
        else:
            logger.warning("⚠️ Le prompt ne contient pas d'exigences de format strictes")
        
        # Chercher le schéma JSON
        if 'json_schema' in content:
            logger.info("✅ Le prompt utilise un schéma JSON")
        else:
            logger.warning("⚠️ Le prompt n'utilise pas de schéma JSON")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la lecture du prompt: {e}")

def main():
    """Fonction principale"""
    logger.info("🔍 Diagnostic des champs vides dans market_analyses")
    logger.info("=" * 60)
    
    analyze_market_analyses()
    test_llm_response_format()
    check_prompt_requirements()
    
    logger.info("\n🎯 Recommandations:")
    logger.info("1. Vérifier que le LLM génère bien tous les champs requis")
    logger.info("2. Ajouter des fallbacks pour générer du contenu si les champs sont vides")
    logger.info("3. Améliorer le prompt pour être plus explicite sur les champs requis")
    logger.info("4. Ajouter des logs détaillés lors de la sauvegarde")

if __name__ == "__main__":
    main()
