#!/usr/bin/env python3
"""
Script de test pour l'API Gemini
Teste la configuration et la connectivité avec Gemini
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_gemini_configuration():
    """Teste la configuration Gemini"""
    print("🔧 Test de configuration Gemini")
    print("=" * 50)
    
    # Vérifier la clé API
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY non configurée")
        print("Ajoutez votre clé Gemini dans le fichier .env:")
        print("GEMINI_API_KEY=votre_clé_gemini_ici")
        return False
    
    print(f"✅ Clé API trouvée: {gemini_api_key[:10]}...")
    
    # Test simple avec Gemini
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
                        "text": "Dis-moi simplement 'Bonjour, Gemini fonctionne!' en français."
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
    """Teste Gemini avec recherche web"""
    print("\n🔍 Test Gemini avec recherche web")
    print("=" * 50)
    
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY non configurée")
        return False
    
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

def main():
    """Fonction principale de test"""
    print("🚀 Test de l'API Gemini")
    print("=" * 60)
    
    # Test 1: Configuration de base
    config_ok = test_gemini_configuration()
    
    if config_ok:
        # Test 2: Recherche web
        search_ok = test_gemini_with_search()
        
        if search_ok:
            print("\n✅ Tous les tests Gemini sont passés!")
            print("🎉 Gemini est correctement configuré et fonctionnel")
        else:
            print("\n⚠️ Configuration de base OK mais problème avec la recherche web")
    else:
        print("\n❌ Problème de configuration Gemini")
        print("Vérifiez votre clé API et votre connexion internet")

if __name__ == "__main__":
    main() 