#!/usr/bin/env python3
"""
Debug de la configuration GPT-5 qui fonctionne
Pour comprendre pourquoi l'API Responses marche dans votre système
"""

import os
from datetime import datetime
from openai import OpenAI

def debug_working_config():
    """Debug de la configuration exacte qui fonctionne"""
    print("🔍 DEBUG CONFIGURATION QUI FONCTIONNE")
    print("=" * 60)
    
    client = OpenAI()
    
    # Configuration EXACTE de votre gpt5_responses_mvp.py
    INSTRUCTIONS = (
        "Tu es un analyste marchés. Texte brut, lisible, concis et actionnable. "
        "Reconnais tendances/corrélations/régimes de volatilité et commente risques/opportunités. "
        "N'invente aucun chiffre. Autorisé: **gras** et emojis sobres (↑, ↓, 🟢, 🔴, ⚠️, 💡). "
        "Structure 3–5 lignes numérotées, puis une conclusion. Pas de titres, pas de tableaux, pas de code."
    )
    
    prompt_text = "Quelle est la situation actuelle du marché boursier ?"
    
    try:
        print("📋 Configuration utilisée:")
        print(f"  - Modèle: gpt-5")
        print(f"  - Instructions: {INSTRUCTIONS[:100]}...")
        print(f"  - Prompt: {prompt_text}")
        print(f"  - Max tokens: 384")
        print(f"  - Timeout: 60s")
        print(f"  - Tool choice: none")
        print(f"  - Text format: {{'format': {{'type': 'text'}}, 'verbosity': 'medium'}}")
        print(f"  - Reasoning: PAS de paramètre")
        
        # Appel EXACT comme dans votre script
        res = client.responses.create(
            model="gpt-5",
            instructions=INSTRUCTIONS,
            input=(
                prompt_text.strip()
                + "\n\nÉcris la RÉPONSE FINALE maintenant en texte brut, 3–5 lignes numérotées, puis une conclusion. "
                  "Commence par: OK –"
            ),
            tool_choice="none",
            text={"format": {"type": "text"}, "verbosity": "medium"},
            max_output_tokens=384,
            timeout=60
            # ⚠️ PAS de paramètre reasoning
        )
        
        print(f"\n✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"🔢 Request ID: {getattr(res, '_request_id', 'N/A')}")
        
        # Analyse détaillée
        if hasattr(res, 'usage') and res.usage:
            usage = res.usage
            print(f"\n📊 Usage détaillé:")
            print(f"  - Input tokens: {getattr(usage, 'input_tokens', 'N/A')}")
            print(f"  - Output tokens: {getattr(usage, 'output_tokens', 'N/A')}")
            print(f"  - Total tokens: {getattr(usage, 'total_tokens', 'N/A')}")
            
            if hasattr(usage, 'output_tokens_details'):
                details = usage.output_tokens_details
                print(f"  - Reasoning tokens: {getattr(details, 'reasoning_tokens', 'N/A')}")
                print(f"  - Text tokens: {getattr(details, 'text_tokens', 'N/A')}")
        
        # Vérifier la structure de sortie
        out = (res.output_text or "").strip()
        if out:
            print(f"\n🎉 SUCCÈS ! Texte extrait:")
            print(f"📏 Longueur: {len(out)} caractères")
            print(f"📝 Contenu: {out[:200]}...")
            
            # Vérifier si c'est bien du texte de marché
            if "OK –" in out:
                print("✅ Format correct: commence par 'OK –'")
            if any(word in out.lower() for word in ["marché", "boursier", "actions", "tendances"]):
                print("✅ Contenu de marché détecté")
            
            return out
        else:
            print(f"\n⚠️ Output text vide - investigation...")
            
            # Explorer la structure
            if hasattr(res, 'output') and res.output:
                print(f"📦 Output items: {len(res.output)}")
                for i, item in enumerate(res.output):
                    print(f"  Item {i}: type={getattr(item, 'type', 'N/A')}")
                    
                    # Essayer d'extraire le contenu
                    if hasattr(item, 'content') and item.content:
                        print(f"    Content: {item.content}")
                    if hasattr(item, 'summary') and item.summary:
                        print(f"    Summary: {item.summary}")
            
            return ""
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return ""

def test_different_prompts():
    """Test avec différents types de prompts"""
    print("\n🔄 TEST AVEC DIFFÉRENTS PROMPTS")
    print("=" * 50)
    
    client = OpenAI()
    
    prompts = [
        "Analyse le marché en 2 phrases. Commence par: OK –",
        "Quelles opportunités sur l'immobilier coté aujourd'hui ?",
        "Dis: test marché OK.",
        "En une phrase: opportunités actions suisses ?"
    ]
    
    INSTRUCTIONS = (
        "Tu es un analyste marchés. Texte brut, lisible, concis et actionnable. "
        "Reconnais tendances/corrélations/régimes de volatilité et commente risques/opportunités. "
        "N'invente aucun chiffre. Autorisé: **gras** et emojis sobres (↑, ↓, 🟢, 🔴, ⚠️, 💡). "
        "Structure 3–5 lignes numérotées, puis une conclusion. Pas de titres, pas de tableaux, pas de code."
    )
    
    for i, prompt in enumerate(prompts):
        print(f"\n📋 Test {i+1}: {prompt[:50]}...")
        print("-" * 40)
        
        try:
            res = client.responses.create(
                model="gpt-5",
                instructions=INSTRUCTIONS,
                input=(
                    prompt.strip()
                    + "\n\nÉcris la RÉPONSE FINALE maintenant en texte brut, 3–5 lignes numérotées, puis une conclusion. "
                      "Commence par: OK –"
                ),
                tool_choice="none",
                text={"format": {"type": "text"}, "verbosity": "medium"},
                max_output_tokens=384,
                timeout=60
            )
            
            output_text = (res.output_text or "").strip()
            if output_text:
                print(f"✅ Succès: {output_text[:100]}...")
            else:
                print(f"⚠️ Vide: output_text est vide")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")

def test_environment_variables():
    """Vérifier les variables d'environnement"""
    print("\n🔍 VÉRIFICATION VARIABLES D'ENVIRONNEMENT")
    print("=" * 50)
    
    env_vars = [
        "OPENAI_API_KEY",
        "MODEL_PRIMARY", 
        "MODEL_SECOND",
        "MAX_OUT",
        "TIMEOUT_S",
        "FALLBACK_CHAT"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "Non définie")
        if var == "OPENAI_API_KEY" and value != "Non définie":
            value = f"{value[:10]}..." if len(value) > 10 else value
        print(f"  {var}: {value}")

def main():
    """Fonction principale"""
    print("🔍 DEBUG COMPLET DE LA CONFIGURATION GPT-5 QUI FONCTIONNE")
    print("=" * 70)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier l'environnement
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY non configurée")
        return
    
    # Vérifier les variables d'environnement
    test_environment_variables()
    
    # Test principal
    result = debug_working_config()
    
    # Tests supplémentaires
    test_different_prompts()
    
    print(f"\n🎉 DEBUG TERMINÉ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if result:
        print("\n🎯 RÉSULTAT: L'API Responses fonctionne !")
        print("🔑 CLÉS IDENTIFIÉES:")
        print("  ✅ Instructions spécifiques et détaillées")
        print("  ✅ Prompt structuré avec demande explicite")
        print("  ✅ Paramètre text={'format': {'type': 'text'}, 'verbosity': 'medium'}")
        print("  ✅ tool_choice='none'")
        print("  ❌ PAS de paramètre reasoning")
        print("  ✅ Timeout et max_output_tokens appropriés")
    else:
        print("\n⚠️ L'API Responses ne fonctionne toujours pas...")

if __name__ == "__main__":
    main()
