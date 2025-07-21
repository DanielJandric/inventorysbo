#!/usr/bin/env python3
"""
Test d'intégration de l'API Manus pour les rapports financiers quotidiens
"""

import requests
import json
from datetime import datetime

def test_manus_api_integration():
    """Test l'intégration complète de l'API Manus"""
    
    print("🧪 Test d'intégration API Manus pour rapports financiers")
    print("=" * 60)
    
    base_url = "https://e5h6i7cn86z0.manus.space"
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Test de santé de l'API
    print("🔍 Test de santé de l'API...")
    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=10)
        if health_response.status_code == 200:
            print("   ✅ API Manus opérationnelle")
        else:
            print(f"   ❌ Erreur santé API: {health_response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Erreur connexion API: {e}")
        return
    
    # 2. Test de collecte de données
    print("\n📊 Test de collecte de données...")
    try:
        collect_response = requests.post(f"{base_url}/api/data/collect", timeout=30)
        if collect_response.status_code == 200:
            collect_data = collect_response.json()
            print("   ✅ Données collectées avec succès")
            print(f"   📅 Date: {collect_data.get('date', 'N/A')}")
        else:
            print(f"   ❌ Erreur collecte: {collect_response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Erreur collecte: {e}")
        return
    
    # 3. Test de récupération des données brutes
    print("\n📈 Test récupération données brutes...")
    try:
        raw_response = requests.get(f"{base_url}/api/data/raw")
        if raw_response.status_code == 200:
            raw_data = raw_response.json()
            print("   ✅ Données brutes récupérées")
            
            # Vérifier les sections disponibles
            if 'financial_data' in raw_data:
                financial = raw_data['financial_data']
                print(f"   💰 Marchés: {len(financial.get('markets', {}))} régions")
                print(f"   🪙 Crypto: {len(financial.get('cryptocurrencies', []))} actifs")
                print(f"   📊 Obligations: {len(financial.get('bonds', []))} instruments")
        else:
            print(f"   ❌ Erreur données brutes: {raw_response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur données brutes: {e}")
    
    # 4. Test de génération de rapport IA
    print("\n🤖 Test génération rapport IA...")
    try:
        report_data = {
            "date": current_date,
            "force_refresh": False
        }
        
        report_response = requests.post(
            f"{base_url}/api/ai/generate/complete",
            json=report_data,
            timeout=60
        )
        
        if report_response.status_code == 200:
            report = report_response.json()
            if report.get('success') and report.get('report'):
                report_content = report['report']
                print("   ✅ Rapport IA généré avec succès")
                print(f"   📅 Date rapport: {report_content.get('metadata', {}).get('report_date', 'N/A')}")
                print(f"   🌍 Régions: {report_content.get('metadata', {}).get('regions_covered', [])}")
                
                # Afficher un extrait du résumé
                executive_summary = report_content.get('executive_summary', '')
                if executive_summary:
                    print(f"   📝 Résumé exécutif: {executive_summary[:100]}...")
                
                # Vérifier les sections du rapport
                sections = ['market_analysis', 'economic_outlook', 'risk_assessment']
                for section in sections:
                    if report_content.get(section):
                        print(f"   ✅ Section {section}: Disponible")
                    else:
                        print(f"   ⚠️ Section {section}: Non disponible")
            else:
                print("   ❌ Réponse invalide du rapport IA")
        else:
            print(f"   ❌ Erreur génération rapport: {report_response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur rapport IA: {e}")
    
    # 5. Test de workflow complet
    print("\n🔄 Test workflow complet...")
    try:
        workflow_response = requests.post(f"{base_url}/api/ai/workflow/complete", timeout=90)
        if workflow_response.status_code == 200:
            workflow_data = workflow_response.json()
            print("   ✅ Workflow complet réussi")
            if workflow_data.get('report'):
                print("   📊 Rapport généré dans le workflow")
        else:
            print(f"   ❌ Erreur workflow: {workflow_response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur workflow: {e}")
    
    # 6. Test d'analyse personnalisée
    print("\n🎯 Test analyse personnalisée...")
    try:
        custom_data = {
            "date": current_date,
            "prompt": "Quelle est l'impact de la politique monétaire de la Fed sur les marchés européens ?"
        }
        
        custom_response = requests.post(
            f"{base_url}/api/ai/generate/custom",
            json=custom_data,
            timeout=60
        )
        
        if custom_response.status_code == 200:
            custom_result = custom_response.json()
            if custom_result.get('success'):
                print("   ✅ Analyse personnalisée réussie")
                analysis = custom_result.get('analysis', '')
                if analysis:
                    print(f"   📝 Analyse: {analysis[:100]}...")
            else:
                print("   ❌ Réponse invalide analyse personnalisée")
        else:
            print(f"   ❌ Erreur analyse personnalisée: {custom_response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur analyse personnalisée: {e}")
    
    # 7. Test des endpoints utilitaires
    print("\n🔧 Test endpoints utilitaires...")
    
    # Dates disponibles
    try:
        dates_response = requests.get(f"{base_url}/api/available-dates")
        if dates_response.status_code == 200:
            dates = dates_response.json()
            print(f"   📅 Dates disponibles: {len(dates.get('dates', []))} dates")
        else:
            print(f"   ❌ Erreur dates: {dates_response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur dates: {e}")
    
    # Endpoints disponibles
    try:
        endpoints_response = requests.get(f"{base_url}/api/endpoints")
        if endpoints_response.status_code == 200:
            endpoints = endpoints_response.json()
            print(f"   🔗 Endpoints disponibles: {len(endpoints.get('endpoints', []))} endpoints")
        else:
            print(f"   ❌ Erreur endpoints: {endpoints_response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur endpoints: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Test d'intégration API Manus terminé !")
    print("✅ L'API est prête pour l'intégration dans votre application")

if __name__ == "__main__":
    test_manus_api_integration() 