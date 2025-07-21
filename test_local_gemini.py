#!/usr/bin/env python3
"""
Test local de la logique Gemini de l'application
"""

import os
import requests
from datetime import datetime

def test_gemini_logic():
    """Test de la logique exacte de l'application"""
    
    print("🔧 Test de la logique Gemini de l'application")
    print("=" * 60)
    
    # Simuler la clé de Render
    gemini_api_key = "AIzaSyD3v6Wpsbmk0TuaOyoKZoY3-UA1zmD0csE"
    
    print(f"✅ Clé Gemini: {gemini_api_key[:10]}...")
    
    # Test exact de la fonction generate_market_briefing_with_gemini()
    try:
        # Prompt exact de l'application
        current_date = datetime.now().strftime('%d/%m/%Y')
        prompt = f"""Recherche en temps réel les données de marché d'aujourd'hui ({current_date}) et génères un briefing complet.

Fais-moi un briefing narratif détaillé et structuré sur la séance des marchés financiers du jour ({current_date}).

STRUCTURE OBLIGATOIRE :

1. MARCHÉS ACTIONS
- USA (S&P 500, NASDAQ, Dow Jones)
- Europe (CAC 40, DAX, FTSE 100)
- Suisse (SMI)
- Autres zones si mouvement significatif

2. OBLIGATIONS SOUVERAINES
- US 10Y, Bund, OAT, BTP
- Confédération suisse
- Spreads et mouvements

3. CRYPTOACTIFS
- BTC, ETH
- Capitalisation globale
- Mouvements liés à la régulation ou aux flux

4. MACROÉCONOMIE & BANQUES CENTRALES
- Statistiques importantes
- Commentaires des banquiers centraux
- Tensions géopolitiques

5. RÉSUMÉ & POINTS DE SURVEILLANCE
- Bullet points clairs
- Signaux faibles ou ruptures de tendance à surveiller

INSTRUCTIONS :
- Utilise tes capacités de recherche web pour des données ACTUELLES
- Cite les sources spécifiques
- Donne des chiffres exacts
- Sois détaillé et complet"""

        # Configuration exacte de l'application
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': gemini_api_key
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "tools": [
                {
                    "googleSearch": {}
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "topK": 40,
                "topP": 0.8,
                "maxOutputTokens": 4000
            }
        }

        print("🔍 Appel API Gemini...")
        response = requests.post(url, headers=headers, json=data, timeout=30)

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ SUCCÈS: Briefing généré")
                print(f"📝 Longueur: {len(content)} caractères")
                print(f"📄 Extrait: {content[:200]}...")
                return True
            else:
                print(f"❌ Réponse invalide: {result}")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"📄 Réponse: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_simple_gemini():
    """Test simple sans recherche web"""
    
    gemini_api_key = "AIzaSyD3v6Wpsbmk0TuaOyoKZoY3-UA1zmD0csE"
    
    print("\n🔍 Test simple sans recherche web")
    print("=" * 50)
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': gemini_api_key
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Dis-moi 'Test simple réussi' en français."
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 100
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Test simple réussi: {content}")
                return True
            else:
                print(f"❌ Réponse invalide: {result}")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test local de la logique Gemini")
    print("=" * 60)
    
    # Test 1: Simple
    simple_ok = test_simple_gemini()
    
    if simple_ok:
        # Test 2: Complet avec recherche web
        complete_ok = test_gemini_logic()
        
        if complete_ok:
            print("\n✅ Tous les tests passent!")
            print("🎉 La logique Gemini fonctionne localement")
            print("🔍 Le problème vient probablement de l'application Render")
        else:
            print("\n⚠️ Test simple OK mais problème avec recherche web")
    else:
        print("\n❌ Problème de base avec Gemini")
        print("Vérifiez la clé ou les permissions") 