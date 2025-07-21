#!/usr/bin/env python3
"""
Test de la clé Gemini spécifique
"""

import requests
import json
from datetime import datetime

def test_gemini_key():
    """Test de la clé Gemini spécifique"""
    
    # Clé Gemini fournie
    gemini_api_key = "AIzaSyD3v6Wpsbmk0TuaOyoKZoY3-UA1zmD0csE"
    
    print("🔧 Test de la clé Gemini")
    print("=" * 50)
    print(f"Clé: {gemini_api_key[:10]}...")
    
    # Test simple
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': gemini_api_key
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Dis-moi simplement 'Test réussi' en français."
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
        print("🔍 Test de connectivité...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Réponse Gemini: {content}")
                return True
            else:
                print(f"❌ Réponse invalide: {result}")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_gemini_with_search():
    """Test avec recherche web"""
    
    gemini_api_key = "AIzaSyD3v6Wpsbmk0TuaOyoKZoY3-UA1zmD0csE"
    
    print("\n🔍 Test avec recherche web")
    print("=" * 50)
    
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': gemini_api_key
    }
    
    current_date = datetime.now().strftime('%d/%m/%Y')
    prompt = f"""Donne-moi un bref résumé des marchés financiers aujourd'hui ({current_date}).
    Utilise tes capacités de recherche web pour des données actuelles.
    Réponds en français en 2-3 phrases maximum."""
    
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
            "maxOutputTokens": 200
        }
    }
    
    try:
        print("🔍 Test avec recherche web...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Réponse avec recherche web: {content}")
                return True
            else:
                print(f"❌ Réponse invalide: {result}")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test de la clé Gemini spécifique")
    print("=" * 60)
    
    # Test 1: Configuration de base
    config_ok = test_gemini_key()
    
    if config_ok:
        # Test 2: Recherche web
        search_ok = test_gemini_with_search()
        
        if search_ok:
            print("\n✅ La clé Gemini fonctionne parfaitement!")
            print("🎉 Le problème vient probablement de l'application")
        else:
            print("\n⚠️ Configuration de base OK mais problème avec la recherche web")
    else:
        print("\n❌ Problème avec la clé Gemini")
        print("Vérifiez la clé ou les permissions") 