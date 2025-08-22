#!/usr/bin/env python3
"""
Test corrigé de l'API Responses de GPT-5
Basé sur les erreurs découvertes lors des premiers tests
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
        
        # Explorer la structure de la réponse
        print(f"\n🔍 STRUCTURE DE LA RÉPONSE:")
        print(f"  - Tous les attributs: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        if hasattr(response, 'output') and response.output:
            print(f"\n📦 OUTPUT DÉTAILLÉ:")
            for i, item in enumerate(response.output):
                print(f"  Item {i}:")
                print(f"    - Type: {getattr(item, 'type', 'N/A')}")
                print(f"    - ID: {getattr(item, 'id', 'N/A')}")
                print(f"    - Summary: {getattr(item, 'summary', 'N/A')}")
                print(f"    - Content: {getattr(item, 'content', 'N/A')}")
                print(f"    - Status: {getattr(item, 'status', 'N/A')}")
                print(f"    - Tous les attributs: {[attr for attr in dir(item) if not attr.startswith('_')]}")
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_with_reasoning_object(client):
    """Test avec le paramètre reasoning comme objet (pas booléen)"""
    print("\n🧠 TEST 2: AVEC RAISONNEMENT (REASONING OBJECT)")
    print("-" * 50)
    
    try:
        response = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste financier. Analyse le marché en détail. Commence par 'ANALYSE:'",
            input="Quelle est la situation actuelle du marché boursier ?",
            max_output_tokens=200,
            reasoning={"type": "auto"}  # Objet au lieu de booléen
        )
        
        print(f"✅ Succès - Status: {getattr(response, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(response, 'output_text', 'N/A')}'")
        
        # Vérifier le raisonnement
        if hasattr(response, 'reasoning') and response.reasoning:
            print(f"\n🧠 RAISONNEMENT:")
            # Vérifier si c'est un objet avec une méthode len ou un attribut
            if hasattr(response.reasoning, '__len__'):
                print(f"  - Nombre d'items: {len(response.reasoning)}")
                for i, item in enumerate(response.reasoning):
                    print(f"    Item {i}:")
                    print(f"      - Type: {getattr(item, 'type', 'N/A')}")
                    print(f"      - Status: {getattr(item, 'status', 'N/A')}")
                    if hasattr(item, 'content') and item.content:
                        print(f"      - Content: {len(item.content)} éléments")
            else:
                print(f"  - Raisonnement: {response.reasoning}")
                print(f"  - Type: {type(response.reasoning)}")
                print(f"  - Attributs: {[attr for attr in dir(response.reasoning) if not attr.startswith('_')]}")
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_with_include_parameters_corrected(client):
    """Test avec les paramètres include corrigés"""
    print("\n🔧 TEST 3: PARAMÈTRES INCLUDE CORRIGÉS")
    print("-" * 50)
    
    # Liste des paramètres include à tester (corrigés)
    include_options = [
        ["reasoning.encrypted_content"],
        ["reasoning.encrypted_content", "code_interpreter_call.outputs"],
        ["file_search_call.results"]
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
                    print(f"  🧠 Reasoning disponible")
                    # Vérifier la structure du raisonnement
                    if hasattr(response.reasoning, '__len__'):
                        print(f"    - Nombre d'items: {len(response.reasoning)}")
                    else:
                        print(f"    - Type: {type(response.reasoning)}")
            
            if "code_interpreter_call.outputs" in include_list:
                print(f"  🔧 Code interpreter outputs demandés")
            
            if "file_search_call.results" in include_list:
                print(f"  📁 File search results demandés")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_streaming_responses_corrected(client):
    """Test du streaming avec l'API Responses (corrigé)"""
    print("\n🌊 TEST 4: STREAMING RESPONSES (CORRIGÉ)")
    print("-" * 50)
    
    try:
        with client.responses.stream(
            model="gpt-5",
            instructions="Tu es un analyste financier. Donne une analyse en temps réel. Commence par 'ANALYSE:'",
            input="Quelle est la situation actuelle du marché boursier ?",
            max_output_tokens=200
        ) as stream:
            
            print("🔄 Streaming en cours...")
            buffer = []
            
            for event in stream:
                print(f"📡 Event: {event.type}")
                if event.type == "response.output_text.delta":
                    delta = getattr(event, 'delta', '')
                    buffer.append(delta)
                    print(f"📝 Delta: '{delta}'")
                elif event.type == "response.completed":
                    print("✅ Streaming terminé")
                    break
            
            final_text = "".join(buffer).strip()
            print(f"\n📋 Texte final: '{final_text}'")
            
    except Exception as e:
        print(f"❌ Erreur streaming: {e}")

def test_extract_text_utility_corrected():
    """Test de la fonction utilitaire d'extraction de texte (corrigée)"""
    print("\n🛠️ TEST 5: FONCTION UTILITAIRE EXTRACT_TEXT (CORRIGÉE)")
    print("-" * 50)
    
    # Simuler une réponse pour tester la fonction
    class MockResponse:
        def __init__(self, output_text=None, output=None, usage=None):
            self.output_text = output_text
            self.output = output
            self.usage = usage
            self._request_id = "test_123"
    
    def extract_text(res) -> str:
        """Fonction utilitaire d'extraction de texte (corrigée)"""
        try:
            # 1) Voie rapide - output_text direct
            if getattr(res, "output_text", None):
                t = (res.output_text or "").strip()
                if t:
                    return t
            
            # 2) Parcourir la structure "output" (avec vérification None)
            chunks = []
            output = getattr(res, "output", None)
            if output and hasattr(output, '__iter__'):
                for item in output:
                    # Messages assistant
                    if getattr(item, "role", "") == "assistant":
                        content = getattr(item, "content", None)
                        if content and hasattr(content, '__iter__'):
                            for part in content:
                                if getattr(part, "type", "") == "output_text" and getattr(part, "text", None):
                                    chunks.append(part.text)
            
            if chunks:
                return "\n".join(chunks).strip()
            
            return ""
            
        except Exception as e:
            print(f"❌ Erreur dans extract_text: {e}")
            return ""
    
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

def test_prompt_optimization():
    """Test de l'optimisation des prompts"""
    print("\n🎯 TEST 6: OPTIMISATION DES PROMPTS")
    print("-" * 50)
    
    base_prompt = "Tu es un analyste financier. Analyse le marché."
    
    # Test avec force_output=True
    optimized_prompt = f"""{base_prompt}

IMPORTANT: Tu DOIS émettre une réponse finale en texte.
- Commence ta réponse par "OK –"
- Sois concis et direct
- Évite de rester dans le raisonnement interne
"""
    
    print(f"📝 Prompt de base: {base_prompt}")
    print(f"📝 Prompt optimisé: {optimized_prompt}")
    print("✅ Prompt optimisé créé avec succès")

def main():
    """Fonction principale de test"""
    print("🚀 TEST CORRIGÉ DE L'API RESPONSES GPT-5")
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
    test_with_reasoning_object(client)
    test_with_include_parameters_corrected(client)
    test_streaming_responses_corrected(client)
    test_extract_text_utility_corrected()
    test_prompt_optimization()
    
    print(f"\n🎉 TESTS TERMINÉS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 RÉSUMÉ DES DÉCOUVERTES:")
    print("  ✅ L'API Responses fonctionne mais output_text est vide")
    print("  ✅ Le paramètre reasoning doit être un objet, pas un booléen")
    print("  ✅ Les logprobs ne sont pas supportés avec les modèles de raisonnement")
    print("  ✅ Le streaming fonctionne mais sans le paramètre text.type")
    print("  ✅ La structure de réponse est complexe et nécessite une extraction robuste")

if __name__ == "__main__":
    main()
