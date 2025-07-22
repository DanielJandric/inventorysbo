#!/usr/bin/env python3
"""
Test des nouvelles APIs Manus
1. https://y0h0i3cqzyko.manus.space/api/report - API de rapport pour les mises à jour des marchés
2. https://ogh5izcelen1.manus.space/ - API de cours de bourse
"""

import requests
import json
from datetime import datetime
import time

def test_market_report_api():
    """Test de l'API de rapport des marchés"""
    
    print("📊 Test API Rapport des Marchés")
    print("=" * 50)
    
    base_url = "https://y0h0i3cqzyko.manus.space"
    
    # Test 1: Endpoint de santé
    print("🔍 Test de santé de l'API...")
    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"   Status: {health_response.status_code}")
        if health_response.status_code == 200:
            print("   ✅ API opérationnelle")
            try:
                health_data = health_response.json()
                print(f"   📊 Données santé: {health_data}")
            except:
                print("   📄 Réponse texte")
        else:
            print(f"   ❌ Erreur: {health_response.text}")
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
    
    # Test 2: Endpoint principal /api/report
    print("\n📈 Test endpoint /api/report...")
    try:
        report_response = requests.get(f"{base_url}/api/report", timeout=30)
        print(f"   Status: {report_response.status_code}")
        
        if report_response.status_code == 200:
            try:
                report_data = report_response.json()
                print("   ✅ Rapport récupéré avec succès")
                print(f"   📊 Type de données: {type(report_data)}")
                
                # Analyser la structure des données
                if isinstance(report_data, dict):
                    print(f"   🔑 Clés disponibles: {list(report_data.keys())}")
                    
                    # Afficher quelques informations clés
                    for key, value in report_data.items():
                        if isinstance(value, (str, int, float)):
                            print(f"   📝 {key}: {value}")
                        elif isinstance(value, list):
                            print(f"   📋 {key}: {len(value)} éléments")
                        elif isinstance(value, dict):
                            print(f"   📊 {key}: {len(value)} sous-clés")
                elif isinstance(report_data, list):
                    print(f"   📋 Liste de {len(report_data)} éléments")
                    if report_data:
                        print(f"   📝 Premier élément: {type(report_data[0])}")
                
            except json.JSONDecodeError:
                print("   📄 Réponse non-JSON")
                print(f"   📝 Contenu: {report_response.text[:200]}...")
        else:
            print(f"   ❌ Erreur: {report_response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Endpoint avec paramètres
    print("\n🎯 Test endpoint avec paramètres...")
    try:
        params = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "format": "json"
        }
        
        param_response = requests.get(f"{base_url}/api/report", params=params, timeout=30)
        print(f"   Status: {param_response.status_code}")
        
        if param_response.status_code == 200:
            print("   ✅ Rapport avec paramètres récupéré")
            try:
                param_data = param_response.json()
                print(f"   📊 Données reçues: {type(param_data)}")
            except:
                print("   📄 Réponse non-JSON")
        else:
            print(f"   ❌ Erreur: {param_response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def test_stock_prices_api():
    """Test de l'API de cours de bourse"""
    
    print("\n\n💹 Test API Cours de Bourse")
    print("=" * 50)
    
    base_url = "https://ogh5izcelen1.manus.space"
    
    # Test 1: Endpoint racine
    print("🔍 Test endpoint racine...")
    try:
        root_response = requests.get(base_url, timeout=10)
        print(f"   Status: {root_response.status_code}")
        
        if root_response.status_code == 200:
            print("   ✅ Endpoint racine accessible")
            try:
                root_data = root_response.json()
                print(f"   📊 Données: {type(root_data)}")
                if isinstance(root_data, dict):
                    print(f"   🔑 Clés: {list(root_data.keys())}")
            except:
                print("   📄 Réponse HTML/texte")
                print(f"   📝 Contenu: {root_response.text[:200]}...")
        else:
            print(f"   ❌ Erreur: {root_response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
    
    # Test 2: Endpoints possibles pour les cours de bourse
    possible_endpoints = [
        "/api/stocks",
        "/api/prices", 
        "/api/market-data",
        "/api/quotes",
        "/stocks",
        "/prices",
        "/market-data"
    ]
    
    print("\n🔍 Test des endpoints possibles...")
    for endpoint in possible_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - Accessible")
                try:
                    data = response.json()
                    print(f"   📊 Type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   🔑 Clés: {list(data.keys())[:5]}...")
                    elif isinstance(data, list):
                        print(f"   📋 Éléments: {len(data)}")
                except:
                    print(f"   📄 Réponse non-JSON")
            elif response.status_code == 404:
                print(f"   ❌ {endpoint} - Non trouvé")
            else:
                print(f"   ⚠️ {endpoint} - Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint} - Erreur: {e}")
    
    # Test 3: Recherche d'endpoints de documentation
    print("\n📚 Test endpoints de documentation...")
    doc_endpoints = [
        "/docs",
        "/api/docs", 
        "/swagger",
        "/api/swagger",
        "/openapi.json",
        "/api/openapi.json"
    ]
    
    for endpoint in doc_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - Documentation trouvée")
                if "swagger" in response.text.lower() or "openapi" in response.text.lower():
                    print(f"   📖 {endpoint} - Documentation API")
            elif response.status_code == 404:
                pass  # Endpoint normalement non trouvé
            else:
                print(f"   ⚠️ {endpoint} - Status {response.status_code}")
        except Exception as e:
            pass  # Ignorer les erreurs de connexion

def test_specific_stock_queries():
    """Test de requêtes spécifiques pour les cours de bourse"""
    
    print("\n\n🎯 Test requêtes spécifiques cours de bourse")
    print("=" * 50)
    
    base_url = "https://ogh5izcelen1.manus.space"
    
    # Test avec des symboles boursiers populaires
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    for symbol in symbols:
        print(f"\n📈 Test pour {symbol}...")
        
        # Test différents formats d'endpoint
        endpoints = [
            f"/api/stocks/{symbol}",
            f"/api/prices/{symbol}",
            f"/stocks/{symbol}",
            f"/prices/{symbol}",
            f"/api/quote/{symbol}",
            f"/quote/{symbol}"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ {endpoint} - Succès")
                    try:
                        data = response.json()
                        print(f"   📊 Données: {type(data)}")
                        if isinstance(data, dict):
                            # Afficher les informations clés
                            for key in ['price', 'symbol', 'name', 'change', 'volume']:
                                if key in data:
                                    print(f"   💰 {key}: {data[key]}")
                    except:
                        print(f"   📄 Réponse non-JSON")
                    break  # Arrêter si on trouve un endpoint qui fonctionne
                elif response.status_code == 404:
                    pass  # Endpoint non trouvé
                else:
                    print(f"   ⚠️ {endpoint} - Status {response.status_code}")
            except Exception as e:
                pass  # Ignorer les erreurs

def test_market_report_integration():
    """Test d'intégration pour l'utilisation dans l'application"""
    
    print("\n\n🔗 Test d'intégration pour l'application")
    print("=" * 50)
    
    report_url = "https://y0h0i3cqzyko.manus.space/api/report"
    stock_url = "https://ogh5izcelen1.manus.space"
    
    # Simuler l'utilisation dans l'application
    print("📊 Simulation mise à jour des marchés...")
    
    try:
        # Récupérer le rapport des marchés
        report_response = requests.get(report_url, timeout=30)
        if report_response.status_code == 200:
            print("   ✅ Rapport des marchés récupéré")
            
            # Simuler l'intégration dans l'application
            try:
                report_data = report_response.json()
                print("   🔄 Intégration dans l'application...")
                
                # Simuler le traitement des données
                if isinstance(report_data, dict):
                    print("   📝 Traitement des données du rapport...")
                    # Ici vous pourriez ajouter votre logique de traitement
                    
            except json.JSONDecodeError:
                print("   ⚠️ Données non-JSON, traitement texte nécessaire")
                
        else:
            print(f"   ❌ Erreur rapport: {report_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur intégration rapport: {e}")
    
    print("\n💹 Simulation mise à jour des cours de bourse...")
    
    # Test avec quelques symboles pour simuler l'intégration
    test_symbols = ["AAPL", "MSFT"]
    
    for symbol in test_symbols:
        try:
            # Essayer différents endpoints
            endpoints = [
                f"{stock_url}/api/stocks/{symbol}",
                f"{stock_url}/stocks/{symbol}",
                f"{stock_url}/api/prices/{symbol}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        print(f"   ✅ {symbol} - Données récupérées")
                        try:
                            data = response.json()
                            print(f"   📊 Format: {type(data)}")
                            # Simuler le traitement
                            print(f"   🔄 Intégration {symbol} dans l'application...")
                        except:
                            print(f"   📄 Format texte pour {symbol}")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"   ❌ Erreur {symbol}: {e}")

def main():
    """Fonction principale de test"""
    
    print("🚀 Test des nouvelles APIs Manus")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: API de rapport des marchés
    test_market_report_api()
    
    # Test 2: API de cours de bourse
    test_stock_prices_api()
    
    # Test 3: Requêtes spécifiques
    test_specific_stock_queries()
    
    # Test 4: Intégration
    test_market_report_integration()
    
    print("\n" + "=" * 60)
    print("🎉 Tests terminés !")
    print("📋 Résumé:")
    print("   • API Rapport: https://y0h0i3cqzyko.manus.space/api/report")
    print("   • API Cours: https://ogh5izcelen1.manus.space/")
    print("   • Vérifiez les résultats ci-dessus pour l'intégration")

if __name__ == "__main__":
    main() 