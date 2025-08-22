#!/usr/bin/env python3
"""
Test complet de l'API Responses de GPT-5 avec tous les paramètres include
Teste les différentes options d'enrichissement des réponses
"""

import os
import sys
import json
from datetime import datetime
from openai import OpenAI

def check_environment():
    """Vérifie la configuration de l'environnement"""
    print("🔍 VÉRIFICATION DE L'ENVIRONNEMENT")
    print("=" * 50)
    
    # Vérifier OpenAI API Key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY non configurée")
        print("💡 Pour configurer :")
        print("   1. Créez un fichier .env avec OPENAI_API_KEY=votre_clé")
        print("   2. Ou exportez la variable : set OPENAI_API_KEY=votre_clé")
        return False
    
    print(f"✅ OPENAI_API_KEY configurée: {openai_key[:10]}...")
    
    # Vérifier la version d'OpenAI
    try:
        import openai
        print(f"✅ Version OpenAI: {openai.__version__}")
    except Exception as e:
        print(f"⚠️ Impossible de vérifier la version OpenAI: {e}")
    
    return True

def test_basic_responses(client):
    """Test de base sans paramètres include"""
    print("\n🎯 TEST 1: RÉPONSE DE BASE (SANS INCLUDE)")
    print("-" * 50)
    
    try:
        response = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste financier. Analyse brièvement le marché actuel en 2-3 phrases. Commence par 'ANALYSE:'",
            input="Quelle est la situation actuelle du marché boursier ?",
            max_output_tokens=150
        )
        
        print(f"✅ Succès - Status: {getattr(response, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(response, 'output_text', 'N/A')}'")
        
        # Afficher les métadonnées
        print(f"\n📊 MÉTADONNÉES:")
        print(f"  - Request ID: {getattr(response, '_request_id', 'N/A')}")
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            print(f"  - Input tokens: {getattr(usage, 'input_tokens', 'N/A')}")
            print(f"  - Output tokens: {getattr(usage, 'output_tokens', 'N/A')}")
            print(f"  - Total tokens: {getattr(usage, 'total_tokens', 'N/A')}")
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_with_reasoning(client):
    """Test avec le paramètre reasoning"""
    print("\n🧠 TEST 2: AVEC RAISONNEMENT (REASONING)")
    print("-" * 50)
    
    try:
        response = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste financier. Analyse le marché en détail. Commence par 'ANALYSE:'",
            input="Quelle est la situation actuelle du marché boursier ?",
            max_output_tokens=200,
            reasoning=True
        )
        
        print(f"✅ Succès - Status: {getattr(response, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(response, 'output_text', 'N/A')}'")
        
        # Vérifier le raisonnement
        if hasattr(response, 'reasoning') and response.reasoning:
            print(f"\n🧠 RAISONNEMENT:")
            for i, item in enumerate(response.reasoning):
                print(f"  Item {i}:")
                print(f"    - Type: {getattr(item, 'type', 'N/A')}")
                print(f"    - Status: {getattr(item, 'status', 'N/A')}")
                if hasattr(item, 'content') and item.content:
                    print(f"    - Content: {len(item.content)} éléments")
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_with_include_parameters(client):
    """Test avec différents paramètres include"""
    print("\n🔧 TEST 3: PARAMÈTRES INCLUDE")
    print("-" * 50)
    
    # Liste des paramètres include à tester
    include_options = [
        ["reasoning.encrypted_content"],
        ["message.output_text.logprobs"],
        ["reasoning.encrypted_content", "message.output_text.logprobs"]
    ]
    
    for i, include_list in enumerate(include_options):
        print(f"\n📋 Test {i+1}: {include_list}")
        print("-" * 30)
        
        try:
            response = client.responses.create(
                model="gpt-5",
                instructions="Tu es un analyste financier. Donne une analyse concise. Commence par 'ANALYSE:'",
                input="Quelle est la situation actuelle du marché boursier ?",
                max_output_tokens=150,
                include=include_list
            )
            
            print(f"✅ Succès - Status: {getattr(response, 'status', 'N/A')}")
            print(f"📝 Output text: '{getattr(response, 'output_text', 'N/A')}'")
            
            # Vérifier les éléments inclus
            if "reasoning.encrypted_content" in include_list:
                if hasattr(response, 'reasoning') and response.reasoning:
                    print(f"  🧠 Reasoning items: {len(response.reasoning)}")
                    for item in response.reasoning:
                        if hasattr(item, 'encrypted_content'):
                            print(f"    - Encrypted content: {getattr(item, 'encrypted_content', 'N/A')}")
            
            if "message.output_text.logprobs" in include_list:
                if hasattr(response, 'output') and response.output:
                    for item in response.output:
                        if hasattr(item, 'logprobs'):
                            print(f"  📊 Logprobs disponibles: {getattr(item, 'logprobs', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_streaming_responses(client):
    """Test du streaming avec l'API Responses"""
    print("\n🌊 TEST 4: STREAMING RESPONSES")
    print("-" * 50)
    
    try:
        with client.responses.stream(
            model="gpt-5",
            instructions="Tu es un analyste financier. Donne une analyse en temps réel. Commence par 'ANALYSE:'",
            input="Quelle est la situation actuelle du marché boursier ?",
            max_output_tokens=200,
            text={"type": "text"}
        ) as stream:
            
            print("🔄 Streaming en cours...")
            buffer = []
            
            for event in stream:
                if event.type == "response.output_text.delta":
                    delta = getattr(event, 'delta', '')
                    buffer.append(delta)
                    print(f"📝 Delta: '{delta}'")
                elif event.type == "response.completed":
                    print("✅ Streaming terminé")
                    break
                else:
                    print(f"📡 Event: {event.type}")
            
            final_text = "".join(buffer).strip()
            print(f"\n📋 Texte final: '{final_text}'")
            
    except Exception as e:
        print(f"❌ Erreur streaming: {e}")

def test_extract_text_utility():
    """Test de la fonction utilitaire d'extraction de texte"""
    print("\n🛠️ TEST 5: FONCTION UTILITAIRE EXTRACT_TEXT")
    print("-" * 50)
    
    # Simuler une réponse pour tester la fonction
    class MockResponse:
        def __init__(self, output_text=None, output=None, usage=None):
            self.output_text = output_text
            self.output = output
            self.usage = usage
            self._request_id = "test_123"
    
    def extract_text(res) -> str:
        """Fonction utilitaire d'extraction de texte"""
        # 1) Voie rapide
        if getattr(res, "output_text", None):
            t = (res.output_text or "").strip()
            if t:
                return t
        
        # 2) Parcourir la structure "output"
        chunks = []
        for item in getattr(res, "output", []):
            # Messages assistant
            if getattr(item, "role", "") == "assistant":
                for part in getattr(item, "content", []):
                    if getattr(part, "type", "") == "output_text" and getattr(part, "text", None):
                        chunks.append(part.text)
        return "\n".join(chunks).strip()
    
    # Test avec output_text
    mock_res1 = MockResponse(output_text="Test de réponse")
    result1 = extract_text(mock_res1)
    print(f"✅ Test output_text: '{result1}'")
    
    # Test avec output structuré
    mock_res2 = MockResponse(
        output=[
            type('MockItem', (), {
                'role': 'assistant',
                'content': [
                    type('MockPart', (), {
                        'type': 'output_text',
                        'text': 'Réponse structurée'
                    })()
                ]
            })()
        ]
    )
    result2 = extract_text(mock_res2)
    print(f"✅ Test output structuré: '{result2}'")
    
    # Test avec réponse vide
    mock_res3 = MockResponse()
    result3 = extract_text(mock_res3)
    print(f"✅ Test réponse vide: '{result3}'")

def main():
    """Fonction principale de test"""
    print("🚀 TEST COMPLET DE L'API RESPONSES GPT-5")
    print("=" * 60)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier l'environnement
    if not check_environment():
        return
    
    # Initialiser le client OpenAI
    try:
        client = OpenAI()
        print("✅ Client OpenAI initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation client OpenAI: {e}")
        return
    
    # Tests
    test_basic_responses(client)
    test_with_reasoning(client)
    test_with_include_parameters(client)
    test_streaming_responses(client)
    test_extract_text_utility()
    
    print(f"\n🎉 TESTS TERMINÉS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
