#!/usr/bin/env python3
"""
Investigation approfondie de l'API Responses de GPT-5
Explore la structure complète pour comprendre pourquoi output_text est vide
"""

import os
import json
from datetime import datetime
from openai import OpenAI

def deep_investigate_response(response):
    """Investigation approfondie de la structure de réponse"""
    print("\n🔍 INVESTIGATION APPROFONDIE DE LA RÉPONSE")
    print("=" * 60)
    
    # 1. Vérifier output_text
    print("📝 VÉRIFICATION OUTPUT_TEXT:")
    print(f"  - output_text: '{getattr(response, 'output_text', 'N/A')}'")
    print(f"  - Type: {type(getattr(response, 'output_text', None))}")
    print(f"  - Est vide: {getattr(response, 'output_text', '') == ''}")
    
    # 2. Explorer la structure output
    print("\n📦 EXPLORATION OUTPUT:")
    if hasattr(response, 'output') and response.output:
        print(f"  - Nombre d'items: {len(response.output)}")
        for i, item in enumerate(response.output):
            print(f"\n  Item {i}:")
            print(f"    - Type: {getattr(item, 'type', 'N/A')}")
            print(f"    - ID: {getattr(item, 'id', 'N/A')}")
            print(f"    - Status: {getattr(item, 'status', 'N/A')}")
            
            # Explorer le contenu
            content = getattr(item, 'content', None)
            if content:
                print(f"    - Content: {content}")
                if hasattr(content, '__iter__'):
                    print(f"    - Nombre d'éléments content: {len(content)}")
                    for j, content_item in enumerate(content):
                        print(f"      Content {j}: {content_item}")
                        if hasattr(content_item, '__dict__'):
                            print(f"        Attributs: {[attr for attr in dir(content_item) if not attr.startswith('_')]}")
            else:
                print(f"    - Content: {content}")
            
            # Explorer summary
            summary = getattr(item, 'summary', None)
            if summary:
                print(f"    - Summary: {summary}")
                if hasattr(summary, '__iter__'):
                    print(f"    - Nombre d'éléments summary: {len(summary)}")
                    for j, summary_item in enumerate(summary):
                        print(f"      Summary {j}: {summary_item}")
    
    # 3. Explorer reasoning
    print("\n🧠 EXPLORATION REASONING:")
    if hasattr(response, 'reasoning') and response.reasoning:
        reasoning = response.reasoning
        print(f"  - Type: {type(reasoning)}")
        print(f"  - Attributs: {[attr for attr in dir(reasoning) if not attr.startswith('_')]}")
        
        # Essayer d'accéder aux attributs
        for attr in ['content', 'encrypted_content', 'status', 'type']:
            if hasattr(reasoning, attr):
                value = getattr(reasoning, attr)
                print(f"    - {attr}: {value}")
                if value and hasattr(value, '__iter__'):
                    print(f"      - Nombre d'éléments: {len(value)}")
    
    # 4. Essayer model_dump pour voir tout le contenu
    print("\n📋 CONTENU COMPLET (MODEL_DUMP):")
    try:
        response_dict = response.model_dump()
        print(f"  - Clés principales: {list(response_dict.keys())}")
        
        # Explorer les sections importantes
        for key in ['output', 'reasoning', 'usage']:
            if key in response_dict:
                print(f"\n  {key.upper()}:")
                print(f"    - Type: {type(response_dict[key])}")
                if response_dict[key]:
                    if isinstance(response_dict[key], list):
                        print(f"    - Nombre d'éléments: {len(response_dict[key])}")
                        for i, item in enumerate(response_dict[key]):
                            print(f"      Item {i}: {item}")
                    else:
                        print(f"    - Contenu: {response_dict[key]}")
        
    except Exception as e:
        print(f"  - Erreur model_dump: {e}")

def test_with_different_instructions(client):
    """Test avec différentes instructions pour forcer la sortie"""
    print("\n🎯 TEST AVEC DIFFÉRENTES INSTRUCTIONS")
    print("=" * 60)
    
    instructions_list = [
        "Tu es un analyste financier. Donne une analyse en 2 phrases maximum. Commence par 'ANALYSE:'",
        "Tu es un analyste financier. Écris UNIQUEMENT 'ANALYSE: Le marché est stable.'",
        "Tu es un analyste financier. Réponds par 'OK' suivi d'une phrase.",
        "Tu es un analyste financier. Donne une réponse courte. Format: ANALYSE: [texte]"
    ]
    
    for i, instructions in enumerate(instructions_list):
        print(f"\n📋 Test {i+1}: Instructions spécifiques")
        print("-" * 40)
        print(f"Instructions: {instructions}")
        
        try:
            response = client.responses.create(
                model="gpt-5",
                instructions=instructions,
                input="Quelle est la situation du marché ?",
                max_output_tokens=100
            )
            
            print(f"✅ Status: {getattr(response, 'status', 'N/A')}")
            print(f"📝 Output text: '{getattr(response, 'output_text', 'N/A')}'")
            
            # Vérifier si on a du texte cette fois
            if getattr(response, 'output_text', ''):
                print("🎉 SUCCÈS: Output text contient du contenu!")
                break
            else:
                print("⚠️ Output text toujours vide")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_without_reasoning(client):
    """Test sans le paramètre reasoning"""
    print("\n🧠 TEST SANS RAISONNEMENT")
    print("=" * 60)
    
    try:
        response = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste financier. Donne une analyse en 2 phrases. Commence par 'ANALYSE:'",
            input="Quelle est la situation du marché ?",
            max_output_tokens=100
            # Pas de paramètre reasoning
        )
        
        print(f"✅ Status: {getattr(response, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(response, 'output_text', 'N/A')}'")
        
        # Explorer la structure
        if hasattr(response, 'output') and response.output:
            print(f"📦 Output items: {len(response.output)}")
            for i, item in enumerate(response.output):
                print(f"  Item {i}: type={getattr(item, 'type', 'N/A')}")
        
        if hasattr(response, 'reasoning') and response.reasoning:
            print(f"🧠 Reasoning présent: {type(response.reasoning)}")
        else:
            print("🧠 Pas de reasoning")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_with_text_parameter(client):
    """Test avec le paramètre text"""
    print("\n📝 TEST AVEC PARAMÈTRE TEXT")
    print("=" * 60)
    
    try:
        response = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste financier. Donne une analyse en 2 phrases. Commence par 'ANALYSE:'",
            input="Quelle est la situation du marché ?",
            max_output_tokens=100,
            text={"type": "text"}  # Spécifier le type de sortie
        )
        
        print(f"✅ Status: {getattr(response, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(response, 'output_text', 'N/A')}'")
        
        # Explorer la structure
        if hasattr(response, 'output') and response.output:
            print(f"📦 Output items: {len(response.output)}")
            for i, item in enumerate(response.output):
                print(f"  Item {i}: type={getattr(item, 'type', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("🔍 INVESTIGATION APPROFONDIE DE L'API RESPONSES GPT-5")
    print("=" * 70)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier l'environnement
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY non configurée")
        return
    
    # Initialiser le client
    try:
        client = OpenAI()
        print("✅ Client OpenAI initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation client: {e}")
        return
    
    # Test de base pour investigation
    print("\n🎯 TEST DE BASE POUR INVESTIGATION")
    print("-" * 50)
    
    try:
        response = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste financier. Donne une analyse en 2 phrases. Commence par 'ANALYSE:'",
            input="Quelle est la situation du marché ?",
            max_output_tokens=100
        )
        
        print(f"✅ Status: {getattr(response, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(response, 'output_text', 'N/A')}'")
        
        # Investigation approfondie
        deep_investigate_response(response)
        
    except Exception as e:
        print(f"❌ Erreur test de base: {e}")
        return
    
    # Tests supplémentaires
    test_with_different_instructions(client)
    test_without_reasoning(client)
    test_with_text_parameter(client)
    
    print(f"\n🎉 INVESTIGATION TERMINÉE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
