#!/usr/bin/env python3
"""Test complet du pipeline d'analyse de marché"""

import os
import asyncio
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_pipeline():
    """Test le pipeline complet d'analyse de marché"""
    print("🧪 Test du Pipeline d'Analyse de Marché")
    print("=" * 60)
    
    # 1. Vérifier les variables d'environnement
    print("\n1️⃣ Vérification des variables d'environnement:")
    required_vars = ['SCRAPINGBEE_API_KEY', 'OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: Configuré ({len(value)} caractères)")
        else:
            print(f"   ❌ {var}: NON CONFIGURÉ")
            all_present = False
    
    if not all_present:
        print("\n❌ Variables d'environnement manquantes. Le worker ne peut pas fonctionner.")
        return
    
    # 2. Tester la connexion à Supabase
    print("\n2️⃣ Test de connexion à Supabase:")
    try:
        from market_analysis_db import get_market_analysis_db, MarketAnalysis
        db = get_market_analysis_db()
        
        if db.is_connected():
            print("   ✅ Connexion à Supabase établie")
            
            # Vérifier les tâches en attente
            latest = db.get_latest_analysis()
            if latest:
                print(f"   ℹ️ Dernière analyse: ID={latest.id}, Status={latest.worker_status}")
            
            pending = db.get_pending_analysis()
            if pending:
                print(f"   ⚠️ Tâche en attente trouvée: ID={pending.id}")
            else:
                print("   ℹ️ Aucune tâche en attente")
        else:
            print("   ❌ Impossible de se connecter à Supabase")
            return
    except Exception as e:
        print(f"   ❌ Erreur Supabase: {e}")
        return
    
    # 3. Tester ScrapingBee
    print("\n3️⃣ Test de ScrapingBee:")
    try:
        from scrapingbee_scraper import get_scrapingbee_scraper
        scraper = get_scrapingbee_scraper()
        scraper.initialize_sync()
        print("   ✅ ScrapingBee initialisé")
        
        # Créer une tâche de test
        print("   🔄 Création d'une tâche de test...")
        task_id = await scraper.create_scraping_task("Test rapide des marchés financiers", 2)
        print(f"   ✅ Tâche créée: {task_id}")
        
        # Exécuter la tâche
        print("   🚀 Exécution de la tâche (peut prendre 30-60 secondes)...")
        result = await scraper.execute_scraping_task(task_id)
        
        if "error" in result:
            print(f"   ❌ Erreur ScrapingBee: {result['error']}")
        else:
            print("   ✅ Résultat obtenu avec succès")
            print(f"   📊 Résumé: {len(result.get('summary', ''))} caractères")
            print(f"   📌 Points clés: {len(result.get('key_points', []))} points")
            print(f"   💡 Insights: {len(result.get('insights', []))} insights")
            
    except Exception as e:
        print(f"   ❌ Erreur ScrapingBee: {e}")
        return
    
    # 4. Tester le worker complet
    print("\n4️⃣ Test du Worker complet:")
    try:
        # Créer une tâche dans la base de données
        print("   📝 Création d'une tâche dans la base de données...")
        new_analysis = MarketAnalysis(
            analysis_type='test',
            worker_status='pending',
            prompt='Test pipeline: Analyse rapide des marchés avec focus IA'
        )
        analysis_id = db.save_analysis(new_analysis)
        
        if analysis_id:
            print(f"   ✅ Tâche créée dans la DB: ID={analysis_id}")
            
            # Simuler le traitement par le worker
            from background_worker import MarketAnalysisWorker
            worker = MarketAnalysisWorker()
            worker.initialize()
            
            print("   🔄 Traitement de la tâche par le worker...")
            task = db.get_pending_analysis()
            if task and task.id == analysis_id:
                await worker.process_task(task)
                
                # Vérifier le résultat
                updated = db.get_latest_analysis()
                if updated and updated.id == analysis_id:
                    print(f"   ✅ Tâche traitée avec succès! Status: {updated.worker_status}")
                    if updated.summary:
                        print(f"   📄 Résumé généré: {len(updated.summary)} caractères")
                else:
                    print("   ❌ Impossible de récupérer la tâche mise à jour")
            else:
                print("   ❌ La tâche n'est pas visible comme 'pending'")
        else:
            print("   ❌ Impossible de créer la tâche dans la DB")
            
    except Exception as e:
        print(f"   ❌ Erreur Worker: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Test terminé")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
