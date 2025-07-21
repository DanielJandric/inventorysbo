#!/usr/bin/env python3
"""
Test d'intégration du rapport Manus
"""

import requests
import json
from datetime import datetime

def test_manus_integration():
    """Test de l'intégration du rapport Manus"""
    
    print("🔍 Test d'intégration du rapport Manus...")
    
    # Configuration
    base_url = "http://localhost:5000"
    
    # Test de l'endpoint
    print(f"\n📊 Test de l'endpoint /api/market-report/manus")
    print("="*60)
    
    try:
        response = requests.get(f"{base_url}/api/market-report/manus", timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            
            if data.get('success') and data.get('report'):
                report = data['report']
                print(f"\n✅ Rapport trouvé:")
                print(f"   - Date: {report.get('date', 'N/A')}")
                print(f"   - Heure: {report.get('time', 'N/A')}")
                print(f"   - Contenu: {len(report.get('content', ''))} caractères")
                print(f"   - Créé le: {report.get('created_at', 'N/A')}")
                
                # Afficher un extrait du contenu
                content = report.get('content', '')
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"\n📝 Extrait du contenu:")
                    print(f"   {preview}")
            else:
                print(f"❌ Aucun rapport disponible: {data.get('message', 'Erreur inconnue')}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Détails: {error_data}")
            except:
                print(f"   Réponse: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("   Assurez-vous que l'application Flask est démarrée")
    except requests.exceptions.Timeout:
        print("❌ Timeout de la requête")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
    
    # Test de la page web
    print(f"\n🌐 Test de la page /markets")
    print("="*60)
    
    try:
        response = requests.get(f"{base_url}/markets", timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page accessible")
            
            # Vérifier si le contenu contient les éléments attendus
            content = response.text
            
            checks = [
                ("Logo carré", "logo-square"),
                ("Rapport de Marché", "Rapport de Marché"),
                ("Actualiser", "Actualiser"),
                ("loadMarketReport", "loadMarketReport"),
                ("/api/market-report/manus", "/api/market-report/manus")
            ]
            
            print(f"\n🔍 Vérifications du template:")
            for check_name, check_value in checks:
                if check_value in content:
                    print(f"   ✅ {check_name}: OK")
                else:
                    print(f"   ❌ {check_name}: Manquant")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS")
    print("="*60)
    
    print("1. Pour tester l'intégration complète:")
    print("   - Démarrez l'application Flask: python app.py")
    print("   - Ouvrez http://localhost:5000/markets")
    print("   - Vérifiez que le rapport s'affiche correctement")
    
    print("\n2. Pour intégrer l'endpoint Manus réel:")
    print("   - Remplacez l'URL dans get_manus_market_report()")
    print("   - Adaptez le format de réponse selon l'API Manus")
    print("   - Testez avec l'endpoint réel")
    
    print("\n3. Fonctionnalités implémentées:")
    print("   ✅ Logo Bonvin carré")
    print("   ✅ Suppression des emojis")
    print("   ✅ Suppression de la section info")
    print("   ✅ Suppression de la fonction manuelle")
    print("   ✅ Endpoint API préparé")
    print("   ✅ Template adapté")
    
    print("\n✅ Test terminé !")

if __name__ == "__main__":
    test_manus_integration() 