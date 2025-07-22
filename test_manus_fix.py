#!/usr/bin/env python3
"""
Script de test pour diagnostiquer les problèmes avec l'API Manus
"""

import requests
import json
from datetime import datetime

def test_manus_market_report():
    """Test de l'API de rapport de marché Manus"""
    print("🔍 Test de l'API Manus Market Report...")
    
    url = "https://y0h0i3cqzyko.manus.space/api/report"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API fonctionnelle")
            print(f"   📊 Contenu disponible: {len(str(data))} caractères")
            
            # Vérifier la structure
            if 'content' in data:
                content = data['content']
                if 'html' in content:
                    html_content = content['html']
                    print(f"   📄 Contenu HTML: {len(html_content)} caractères")
                    print(f"   📄 Début du contenu: {html_content[:200]}...")
                else:
                    print(f"   ❌ Pas de contenu HTML trouvé")
            else:
                print(f"   ❌ Structure inattendue: {list(data.keys())}")
            
            return data
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   📄 Réponse: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None

def test_manus_stock_api():
    """Test de l'API de prix d'actions Manus"""
    print("\n🔍 Test de l'API Manus Stock...")
    
    url = "https://ogh5izcelen1.manus.space/"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"   ✅ API fonctionnelle")
            print(f"   📊 Contenu disponible: {len(content)} caractères")
            print(f"   📄 Début du contenu: {content[:200]}...")
            
            # Chercher des informations sur les actions
            if 'AAPL' in content or 'stock' in content.lower():
                print(f"   ✅ Contenu semble contenir des données boursières")
            else:
                print(f"   ⚠️ Contenu ne semble pas contenir de données boursières")
            
            return content
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None

def test_manus_integration():
    """Test de l'intégration Manus dans l'application"""
    print("\n🔍 Test de l'intégration Manus...")
    
    try:
        from manus_integration import generate_market_briefing_manus, get_stock_price_manus
        
        # Test du briefing de marché
        print("   📊 Test du briefing de marché...")
        briefing = generate_market_briefing_manus()
        print(f"   Status: {briefing.get('status')}")
        if briefing.get('status') == 'success':
            content = briefing.get('briefing', {}).get('content', '')
            print(f"   Contenu: {len(content)} caractères")
            if content:
                print(f"   Début: {content[:200]}...")
            else:
                print(f"   ❌ Contenu vide")
        else:
            print(f"   ❌ Erreur: {briefing.get('message')}")
        
        # Test du prix d'action
        print("   💰 Test du prix d'action...")
        stock_data = get_stock_price_manus('AAPL', None, 'test', force_refresh=True)
        if stock_data:
            print(f"   ✅ Données récupérées: {stock_data.get('price')} {stock_data.get('currency')}")
        else:
            print(f"   ❌ Aucune donnée récupérée")
            
    except ImportError as e:
        print(f"   ❌ Module manus_integration non trouvé: {e}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Diagnostic des APIs Manus")
    print("=" * 50)
    
    # Test des APIs directement
    market_data = test_manus_market_report()
    stock_data = test_manus_stock_api()
    
    # Test de l'intégration
    test_manus_integration()
    
    print("\n" + "=" * 50)
    print("✅ Diagnostic terminé") 