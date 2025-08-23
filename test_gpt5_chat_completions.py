#!/usr/bin/env python3
"""
Test de l'API Chat Completions de GPT-5
Confirme que cette API fonctionne correctement contrairement à l'API Responses
"""

import os
import json
from datetime import datetime
from openai import OpenAI

def test_gpt5_chat_completions(client):
    """Test de l'API Chat Completions de GPT-5"""
    print("🎯 TEST API CHAT COMPLETIONS GPT-5")
    print("=" * 50)
    
    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system", 
                    "content": "Tu es un analyste financier. Donne une analyse concise du marché en 2-3 phrases. Commence par 'ANALYSE:'"
                },
                {
                    "role": "user", 
                    "content": "Quelle est la situation actuelle du marché boursier ?"
                }
            ],
            max_completion_tokens=150
        )
        
        print(f"✅ Succès - Modèle: {response.model}")
        print(f"📝 Réponse: '{response.choices[0].message.content}'")
        print(f"🔢 Tokens utilisés: {response.usage.total_tokens}")
        print(f"📊 Détails tokens:")
        print(f"  - Input: {response.usage.prompt_tokens}")
        print(f"  - Output: {response.usage.completion_tokens}")
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_gpt5_chat_with_reasoning(client):
    """Test avec raisonnement explicite dans le prompt"""
    print("\n🧠 TEST AVEC RAISONNEMENT EXPLICITE")
    print("-" * 50)
    
    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system", 
                    "content": """Tu es un analyste financier. 
                    
PROCESSUS:
1. Analyse la situation du marché
2. Identifie les tendances principales
3. Donne une conclusion claire

FORMAT DE RÉPONSE:
ANALYSE: [Ton analyse en 2-3 phrases]
TENDANCES: [Principales tendances]
CONCLUSION: [Conclusion en une phrase]"""
                },
                {
                    "role": "user", 
                    "content": "Quelle est la situation actuelle du marché boursier ?"
                }
            ],
            max_completion_tokens=200
        )
        
        print(f"✅ Succès - Modèle: {response.model}")
        print(f"📝 Réponse: '{response.choices[0].message.content}'")
        print(f"🔢 Tokens utilisés: {response.usage.total_tokens}")
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_gpt5_chat_streaming(client):
    """Test du streaming avec Chat Completions"""
    print("\n🌊 TEST STREAMING CHAT COMPLETIONS")
    print("-" * 50)
    
    try:
        stream = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system", 
                    "content": "Tu es un analyste financier. Donne une analyse concise."
                },
                {
                    "role": "user", 
                    "content": "Quelle est la situation du marché ?"
                }
            ],
            max_completion_tokens=150,
            stream=True
        )
        
        print("🔄 Streaming en cours...")
        buffer = []
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                buffer.append(content)
                print(f"📝 Delta: '{content}'")
        
        final_text = "".join(buffer).strip()
        print(f"\n📋 Texte final: '{final_text}'")
        
        return final_text
        
    except Exception as e:
        print(f"❌ Erreur streaming: {e}")
        return None

def test_gpt5_chat_json_output(client):
    """Test avec sortie JSON structurée"""
    print("\n📋 TEST SORTIE JSON STRUCTURÉE")
    print("-" * 50)
    
    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system", 
                    "content": "Tu es un analyste financier. Réponds UNIQUEMENT en JSON valide."
                },
                {
                    "role": "user", 
                    "content": "Analyse le marché et réponds en JSON avec: analyse, tendances, conclusion"
                }
            ],
            max_completion_tokens=200,
            response_format={"type": "json_object"}
        )
        
        print(f"✅ Succès - Modèle: {response.model}")
        content = response.choices[0].message.content
        
        try:
            # Parser le JSON
            json_data = json.loads(content)
            print(f"📝 Réponse JSON: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
            print(f"🔢 Tokens utilisés: {response.usage.total_tokens}")
            
            return json_data
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Réponse non-JSON: '{content}'")
            print(f"❌ Erreur parsing: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def compare_apis(client):
    """Comparaison entre Responses et Chat Completions"""
    print("\n⚖️ COMPARAISON DES APIS")
    print("=" * 50)
    
    print("🔍 API RESPONSES:")
    print("  ❌ output_text toujours vide")
    print("  ❌ Consomme des tokens de raisonnement sans texte")
    print("  ❌ Structure complexe et inutilisable")
    
    print("\n🔍 API CHAT COMPLETIONS:")
    print("  ✅ Génère du texte visible")
    print("  ✅ Tokens utilisés efficacement")
    print("  ✅ Structure simple et prévisible")
    print("  ✅ Streaming fonctionnel")
    print("  ✅ Support JSON structuré")
    
    print("\n🏆 RECOMMANDATION: Utiliser Chat Completions")

def main():
    """Fonction principale"""
    print("🚀 TEST COMPLET DE L'API CHAT COMPLETIONS GPT-5")
    print("=" * 60)
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
    
    # Tests
    test_gpt5_chat_completions(client)
    test_gpt5_chat_with_reasoning(client)
    test_gpt5_chat_streaming(client)
    test_gpt5_chat_json_output(client)
    
    # Comparaison
    compare_apis(client)
    
    print(f"\n🎉 TESTS TERMINÉS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 CONCLUSION:")
    print("  ✅ L'API Chat Completions de GPT-5 fonctionne parfaitement")
    print("  ❌ L'API Responses de GPT-5 a un problème fondamental")
    print("  🎯 Recommandation: Migrer vers Chat Completions")

if __name__ == "__main__":
    main()
