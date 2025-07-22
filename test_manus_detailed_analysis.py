#!/usr/bin/env python3
"""
Analyse détaillée des nouvelles APIs Manus
Analyse le contenu exact des réponses pour comprendre la structure des données
"""

import requests
import json
from datetime import datetime

def analyze_market_report_content():
    """Analyse détaillée du contenu de l'API de rapport des marchés"""
    
    print("📊 Analyse détaillée - API Rapport des Marchés")
    print("=" * 60)
    
    url = "https://y0h0i3cqzyko.manus.space/api/report"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Données récupérées avec succès")
            print(f"📅 Timestamp: {data.get('api_call_timestamp', 'N/A')}")
            print(f"🔄 Fraîcheur: {data.get('data_freshness', 'N/A')}")
            print(f"⏱️ Temps de génération: {data.get('generation_time', 'N/A')}")
            
            # Analyser les informations système
            print("\n🔧 Informations système:")
            system_info = data.get('system_info', {})
            for key, value in system_info.items():
                print(f"   {key}: {value}")
            
            # Analyser les informations API
            print("\n📡 Informations API:")
            api_info = data.get('api_info', {})
            for key, value in api_info.items():
                print(f"   {key}: {value}")
            
            # Analyser les informations de cache
            print("\n💾 Informations de cache:")
            cache_info = data.get('cache_info', {})
            for key, value in cache_info.items():
                print(f"   {key}: {value}")
            
            # Analyser le rapport principal
            print("\n📋 Contenu du rapport:")
            report = data.get('report', {})
            
            if isinstance(report, dict):
                print(f"   📊 Sections disponibles: {list(report.keys())}")
                
                for section_name, section_content in report.items():
                    print(f"\n   📝 Section: {section_name}")
                    
                    if isinstance(section_content, str):
                        print(f"      Type: Texte ({len(section_content)} caractères)")
                        print(f"      Extrait: {section_content[:200]}...")
                    elif isinstance(section_content, dict):
                        print(f"      Type: Objet ({len(section_content)} clés)")
                        print(f"      Clés: {list(section_content.keys())}")
                        
                        # Afficher quelques exemples
                        for key, value in list(section_content.items())[:3]:
                            if isinstance(value, str):
                                print(f"      {key}: {value[:100]}...")
                            else:
                                print(f"      {key}: {type(value)}")
                    elif isinstance(section_content, list):
                        print(f"      Type: Liste ({len(section_content)} éléments)")
                        if section_content:
                            print(f"      Premier élément: {type(section_content[0])}")
                    else:
                        print(f"      Type: {type(section_content)}")
            
            # Sauvegarder les données pour analyse
            with open('market_report_sample.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Données sauvegardées dans 'market_report_sample.json'")
            
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"📄 Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def analyze_stock_api_content():
    """Analyse détaillée du contenu de l'API de cours de bourse"""
    
    print("\n\n💹 Analyse détaillée - API Cours de Bourse")
    print("=" * 60)
    
    base_url = "https://ogh5izcelen1.manus.space"
    
    # Test 1: Endpoint racine
    print("🔍 Analyse endpoint racine...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ Endpoint racine accessible")
            print(f"📄 Type de contenu: {response.headers.get('content-type', 'N/A')}")
            
            # Analyser le contenu HTML
            content = response.text
            if '<html' in content.lower():
                print("📄 Contenu HTML détecté")
                
                # Extraire les informations utiles du HTML
                if 'title' in content:
                    title_start = content.find('<title>') + 7
                    title_end = content.find('</title>')
                    if title_start > 7 and title_end > title_start:
                        title = content[title_start:title_end]
                        print(f"📝 Titre: {title}")
                
                # Chercher des informations sur l'API
                if 'api' in content.lower():
                    print("🔗 Informations API trouvées dans le HTML")
                
                # Sauvegarder le HTML
                with open('stock_api_homepage.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print("💾 Page d'accueil sauvegardée dans 'stock_api_homepage.html'")
            else:
                print("📄 Contenu non-HTML")
                print(f"📝 Extrait: {content[:200]}...")
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Endpoints spécifiques
    print("\n📈 Test endpoints spécifiques...")
    
    endpoints_to_test = [
        "/api/stocks/AAPL",
        "/api/prices/AAPL", 
        "/stocks/AAPL",
        "/prices/AAPL"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🔍 Test {endpoint}...")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Succès")
                print(f"   📄 Type: {response.headers.get('content-type', 'N/A')}")
                
                content = response.text
                
                # Essayer de parser comme JSON
                try:
                    json_data = response.json()
                    print(f"   📊 JSON valide")
                    print(f"   🔑 Clés: {list(json_data.keys()) if isinstance(json_data, dict) else 'Liste'}")
                    
                    # Sauvegarder le JSON
                    filename = f"stock_data_{endpoint.replace('/', '_')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    print(f"   💾 Sauvegardé dans '{filename}'")
                    
                except json.JSONDecodeError:
                    print(f"   📄 Contenu non-JSON")
                    
                    # Analyser le contenu HTML
                    if '<html' in content.lower():
                        print(f"   📄 Contenu HTML")
                        
                        # Chercher des informations utiles
                        if 'price' in content.lower():
                            print(f"   💰 Informations de prix trouvées")
                        if 'stock' in content.lower():
                            print(f"   📈 Informations d'actions trouvées")
                        
                        # Sauvegarder le HTML
                        filename = f"stock_html_{endpoint.replace('/', '_')}.html"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"   💾 Sauvegardé dans '{filename}'")
                    else:
                        print(f"   📝 Extrait: {content[:200]}...")
                        
                        # Sauvegarder le texte
                        filename = f"stock_text_{endpoint.replace('/', '_')}.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"   💾 Sauvegardé dans '{filename}'")
                        
            elif response.status_code == 404:
                print(f"   ❌ Endpoint non trouvé")
            else:
                print(f"   ⚠️ Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    # Test 3: Documentation API
    print("\n📚 Analyse documentation API...")
    
    doc_endpoints = [
        "/docs",
        "/api/docs",
        "/swagger",
        "/api/swagger"
    ]
    
    for endpoint in doc_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} - Documentation accessible")
                
                content = response.text
                if 'swagger' in content.lower() or 'openapi' in content.lower():
                    print(f"   📖 Documentation Swagger/OpenAPI")
                    
                    # Sauvegarder la documentation
                    filename = f"api_docs_{endpoint.replace('/', '_')}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"   💾 Sauvegardé dans '{filename}'")
                    
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Non trouvé")
            else:
                print(f"⚠️ {endpoint} - Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Erreur: {e}")

def test_integration_scenarios():
    """Test des scénarios d'intégration pour l'application"""
    
    print("\n\n🔗 Scénarios d'intégration pour l'application")
    print("=" * 60)
    
    # Scénario 1: Mise à jour des rapports de marchés
    print("📊 Scénario 1: Mise à jour des rapports de marchés")
    print("   Objectif: Intégrer l'API de rapport dans votre application")
    
    report_url = "https://y0h0i3cqzyko.manus.space/api/report"
    
    try:
        response = requests.get(report_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            report = data.get('report', {})
            
            print("   ✅ Données disponibles pour intégration:")
            
            if isinstance(report, dict):
                for section_name, section_content in report.items():
                    print(f"   📝 Section '{section_name}': {type(section_content)}")
                    
                    if isinstance(section_content, str):
                        # Simuler l'intégration dans votre application
                        print(f"      💡 Utilisation: Affichage dans l'interface utilisateur")
                        print(f"      📏 Longueur: {len(section_content)} caractères")
                    elif isinstance(section_content, dict):
                        print(f"      💡 Utilisation: Traitement des données structurées")
                        print(f"      🔑 Données: {list(section_content.keys())}")
                    elif isinstance(section_content, list):
                        print(f"      💡 Utilisation: Liste d'éléments à traiter")
                        print(f"      📋 Nombre d'éléments: {len(section_content)}")
            
            print("\n   🔄 Recommandations d'intégration:")
            print("      • Utiliser les données pour les mises à jour automatiques")
            print("      • Intégrer dans votre système de rapports")
            print("      • Mettre en cache les données pour optimiser les performances")
            
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Scénario 2: Mise à jour des cours de bourse
    print("\n💹 Scénario 2: Mise à jour des cours de bourse")
    print("   Objectif: Intégrer l'API de cours dans votre application")
    
    stock_url = "https://ogh5izcelen1.manus.space"
    
    # Test avec quelques symboles
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in test_symbols:
        print(f"\n   📈 Test intégration pour {symbol}...")
        
        endpoints = [
            f"/api/stocks/{symbol}",
            f"/stocks/{symbol}",
            f"/api/prices/{symbol}"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{stock_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    print(f"      ✅ {endpoint} - Données disponibles")
                    
                    # Analyser le type de données
                    try:
                        data = response.json()
                        print(f"      📊 Format JSON - {len(data)} clés" if isinstance(data, dict) else f"      📊 Format JSON - Liste")
                    except:
                        print(f"      📄 Format HTML/Texte")
                    
                    print(f"      💡 Utilisation: Mise à jour des prix en temps réel")
                    break
                    
            except Exception as e:
                continue
    
    print("\n   🔄 Recommandations d'intégration:")
    print("      • Utiliser pour les mises à jour de prix en temps réel")
    print("      • Intégrer dans votre système de gestion de portefeuille")
    print("      • Mettre en place un système de cache pour optimiser les performances")

def main():
    """Fonction principale"""
    
    print("🔍 Analyse détaillée des APIs Manus")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Analyse 1: API de rapport des marchés
    analyze_market_report_content()
    
    # Analyse 2: API de cours de bourse
    analyze_stock_api_content()
    
    # Analyse 3: Scénarios d'intégration
    test_integration_scenarios()
    
    print("\n" + "=" * 60)
    print("🎉 Analyse terminée !")
    print("📋 Fichiers générés:")
    print("   • market_report_sample.json - Données du rapport")
    print("   • stock_api_homepage.html - Page d'accueil API cours")
    print("   • stock_data_*.json - Données de cours (si disponibles)")
    print("   • stock_html_*.html - Pages HTML (si disponibles)")
    print("   • api_docs_*.html - Documentation API (si disponible)")

if __name__ == "__main__":
    main() 