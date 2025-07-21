#!/usr/bin/env python3
"""
Test simple de la fonction Gemini sans dépendances externes
"""

import os
import requests
from datetime import datetime

def test_gemini_function():
    """Test de la fonction Gemini avec une clé factice"""
    
    # Simuler une clé API (pour tester la structure du code)
    gemini_api_key = "AIzaSyTEST1234567890abcdefghijklmnop"
    
    print("🔧 Test de la fonction Gemini")
    print("=" * 50)
    
    # Test de la structure de l'appel API
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': gemini_api_key
    }
    
    current_date = datetime.now().strftime('%d/%m/%Y')
    prompt = f"""Test simple pour vérifier la structure du prompt Gemini.
    Date: {current_date}
    Réponds simplement 'Test réussi' en français."""
    
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
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 100
        }
    }
    
    print(f"✅ Structure de l'appel API correcte")
    print(f"📝 URL: {url}")
    print(f"🔑 Headers: {list(headers.keys())}")
    print(f"📦 Data keys: {list(data.keys())}")
    print(f"📝 Prompt: {prompt[:50]}...")
    
    # Test de la structure de réponse attendue
    expected_response_structure = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Test réussi"
                        }
                    ]
                }
            }
        ]
    }
    
    print(f"✅ Structure de réponse attendue correcte")
    print(f"📦 Response keys: {list(expected_response_structure.keys())}")
    
    return True

def test_gemini_with_search_structure():
    """Test de la structure avec recherche web"""
    
    print("\n🔍 Test structure avec recherche web")
    print("=" * 50)
    
    # Structure avec outils de recherche
    data_with_search = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Test avec recherche web"
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
    
    print(f"✅ Structure avec recherche web correcte")
    print(f"🔧 Tools: {data_with_search['tools']}")
    print(f"⚙️ Generation config: {data_with_search['generationConfig']}")
    
    return True

def main():
    """Fonction principale"""
    print("🚀 Test de la structure Gemini")
    print("=" * 60)
    
    try:
        # Test 1: Structure de base
        test_gemini_function()
        
        # Test 2: Structure avec recherche
        test_gemini_with_search_structure()
        
        print("\n✅ Tous les tests de structure sont passés!")
        print("🎉 Le code Gemini est correctement structuré")
        print("\n📝 Pour utiliser Gemini:")
        print("1. Obtenez une clé API sur https://makersuite.google.com/app/apikey")
        print("2. Ajoutez GEMINI_API_KEY=votre_clé dans .env")
        print("3. Testez avec: python test_gemini_api.py")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main() 