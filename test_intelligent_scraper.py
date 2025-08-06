#!/usr/bin/env python3
"""
Test du scraper intelligent
"""
import asyncio
import json
from intelligent_scraper import IntelligentScraper

async def test_scraper():
    """Test complet du scraper intelligent"""
    print("🧪 Test du Scraper Intelligent")
    print("=" * 50)
    
    # Initialiser le scraper
    scraper = IntelligentScraper()
    await scraper.initialize()
    
    try:
        # Test 1: Créer une tâche
        print("\n📋 Test 1: Création de tâche")
        task_id = await scraper.create_scraping_task(
            "Tesla stock price today latest news earnings",
            num_results=3
        )
        print(f"✅ Tâche créée: {task_id}")
        
        # Test 2: Exécuter la tâche
        print("\n🚀 Test 2: Exécution de la tâche")
        result = await scraper.execute_scraping_task(task_id)
        
        if "error" in result:
            print(f"❌ Erreur: {result['error']}")
            return
        
        print("✅ Tâche exécutée avec succès")
        print(f"📊 Résultats:")
        print(f"   📝 Résumé: {result.get('summary', 'N/A')[:200]}...")
        print(f"   📈 Points clés: {len(result.get('key_points', []))}")
        print(f"   💡 Insights: {len(result.get('insights', []))}")
        print(f"   🎯 Recommandations: {len(result.get('recommendations', []))}")
        print(f"   📚 Sources: {len(result.get('sources', []))}")
        print(f"   🎯 Score de confiance: {result.get('confidence_score', 0)}")
        
        # Test 3: Vérifier le statut
        print("\n📊 Test 3: Vérification du statut")
        task = await scraper.get_task_status(task_id)
        if task:
            print(f"✅ Statut: {task.status}")
            print(f"   Créé: {task.created_at}")
            print(f"   Terminé: {task.completed_at}")
        else:
            print("❌ Tâche non trouvée")
        
        # Test 4: Test direct de scraping
        print("\n🔍 Test 4: Scraping direct")
        scraped_data = await scraper.search_and_scrape("Apple stock price today", num_results=2)
        print(f"✅ {len(scraped_data)} pages scrapées")
        
        for i, data in enumerate(scraped_data):
            print(f"   📄 {i+1}. {data.title}")
            print(f"      URL: {data.url}")
            print(f"      Contenu: {len(data.content)} caractères")
        
        # Test 5: Traitement LLM
        print("\n🤖 Test 5: Traitement LLM")
        if scraped_data:
            llm_result = await scraper.process_with_llm(
                "Analysez les informations sur Apple et donnez-moi un résumé",
                scraped_data
            )
            print(f"✅ Traitement LLM terminé")
            print(f"   📝 Résumé: {llm_result.get('summary', 'N/A')[:150]}...")
            print(f"   📈 Points clés: {len(llm_result.get('key_points', []))}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
    
    finally:
        await scraper.cleanup()
        print("\n🧹 Scraper nettoyé")

def test_sync():
    """Test synchrone pour vérifier l'import"""
    print("🔧 Test d'import synchrone")
    try:
        from intelligent_scraper import IntelligentScraper
        scraper = IntelligentScraper()
        print("✅ Import réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Démarrage des tests du scraper intelligent")
    
    # Test d'import
    if test_sync():
        # Test asynchrone
        asyncio.run(test_scraper())
    else:
        print("❌ Impossible de continuer les tests") 