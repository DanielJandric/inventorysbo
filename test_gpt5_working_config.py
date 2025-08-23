#!/usr/bin/env python3
"""
Test de la configuration GPT-5 qui FONCTIONNE
Basé sur gpt5_responses_mvp.py qui génère vos rapports de marché
"""

import os
from datetime import datetime
from openai import OpenAI

def test_working_config():
    """Test avec la configuration exacte qui fonctionne pour vos rapports"""
    print("🎯 TEST CONFIGURATION QUI FONCTIONNE (gpt5_responses_mvp.py)")
    print("=" * 70)
    
    client = OpenAI()
    
    INSTRUCTIONS = (
        "Tu es un analyste marchés. Texte brut, lisible, concis et actionnable. "
        "Reconnais tendances/corrélations/régimes de volatilité et commente risques/opportunités. "
        "N'invente aucun chiffre. Autorisé: **gras** et emojis sobres (↑, ↓, 🟢, 🔴, ⚠️, 💡). "
        "Structure 3–5 lignes numérotées, puis une conclusion. Pas de titres, pas de tableaux, pas de code."
    )
    
    prompt_text = "Quelle est la situation actuelle du marché boursier ?"
    
    try:
        # Configuration EXACTE de votre code qui fonctionne
        res = client.responses.create(
            model="gpt-5",
            instructions=INSTRUCTIONS,
            input=(
                prompt_text.strip()
                + "\n\nÉcris la RÉPONSE FINALE maintenant en texte brut, 3–5 lignes numérotées, puis une conclusion. "
                  "Commence par: OK –"
            ),
            tool_choice="none",
            text={"format": {"type": "text"}, "verbosity": "medium"},  # ← PARAMÈTRE CLÉ !
            max_output_tokens=384,
            timeout=60
            # ⚠️ PAS de paramètre 'reasoning' ← C'EST LA CLÉ !
        )
        
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"🔢 Request ID: {getattr(res, '_request_id', 'N/A')}")
        
        if hasattr(res, 'usage') and res.usage:
            usage = res.usage
            print(f"📊 Usage:")
            print(f"  - Input tokens: {getattr(usage, 'input_tokens', 'N/A')}")
            print(f"  - Output tokens: {getattr(usage, 'output_tokens', 'N/A')}")
            print(f"  - Total tokens: {getattr(usage, 'total_tokens', 'N/A')}")
            
            # Vérifier les détails des tokens de sortie
            if hasattr(usage, 'output_tokens_details'):
                details = usage.output_tokens_details
                print(f"  - Reasoning tokens: {getattr(details, 'reasoning_tokens', 'N/A')}")
                print(f"  - Text tokens: {getattr(details, 'text_tokens', 'N/A')}")
        
        # Tester l'extraction de texte
        out = (res.output_text or "").strip()
        if out:
            print(f"\n🎉 SUCCÈS ! Texte extrait: '{out}'")
            print(f"📏 Longueur: {len(out)} caractères")
            return out
        else:
            print(f"\n⚠️ Output text vide, vérifions la structure...")
            
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

def test_multiple_models():
    """Test avec différents modèles GPT-5"""
    print("\n🔄 TEST AVEC DIFFÉRENTS MODÈLES")
    print("=" * 50)
    
    models = [
        "gpt-5",
        "gpt-5-2025-08-07"
    ]
    
    client = OpenAI()
    
    for model in models:
        print(f"\n📋 Test avec {model}")
        print("-" * 30)
        
        try:
            res = client.responses.create(
                model=model,
                instructions="Tu es un analyste marchés. Réponds brièvement.",
                input="Analyse le marché en 2 phrases. Commence par: OK –",
                tool_choice="none",
                text={"format": {"type": "text"}, "verbosity": "medium"},
                max_output_tokens=200
                # PAS de reasoning !
            )
            
            output_text = (res.output_text or "").strip()
            print(f"✅ {model}: '{output_text}'")
            
        except Exception as e:
            print(f"❌ {model}: {e}")

def test_reasoning_vs_no_reasoning():
    """Test comparatif avec et sans reasoning"""
    print("\n⚖️ TEST COMPARATIF: AVEC ET SANS REASONING")
    print("=" * 60)
    
    client = OpenAI()
    prompt = "Analyse du marché en 1 phrase. Commence par: OK –"
    
    # Test SANS reasoning (votre config qui marche)
    print("\n📋 SANS reasoning (config qui marche)")
    print("-" * 40)
    try:
        res1 = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés.",
            input=prompt,
            tool_choice="none",
            text={"format": {"type": "text"}, "verbosity": "medium"},
            max_output_tokens=200
            # PAS de reasoning
        )
        output1 = (res1.output_text or "").strip()
        print(f"✅ Sans reasoning: '{output1}'")
        
    except Exception as e:
        print(f"❌ Sans reasoning: {e}")
    
    # Test AVEC reasoning (ce qui ne marche pas)
    print("\n📋 AVEC reasoning (config qui ne marche pas)")
    print("-" * 40)
    try:
        res2 = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés.",
            input=prompt,
            tool_choice="none",
            text={"format": {"type": "text"}, "verbosity": "medium"},
            max_output_tokens=200,
            reasoning={"effort": "medium"}  # AVEC reasoning
        )
        output2 = (res2.output_text or "").strip()
        print(f"✅ Avec reasoning: '{output2}'")
        
    except Exception as e:
        print(f"❌ Avec reasoning: {e}")

def main():
    """Fonction principale"""
    print("🔍 TEST DE LA CONFIGURATION GPT-5 QUI FONCTIONNE")
    print("=" * 70)
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier l'environnement
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY non configurée")
        return
    
    # Tests
    result = test_working_config()
    test_multiple_models()
    test_reasoning_vs_no_reasoning()
    
    print(f"\n🎉 TESTS TERMINÉS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if result:
        print("\n🎯 CONCLUSION: La configuration fonctionne !")
        print("🔑 CLÉS DU SUCCÈS:")
        print("  ✅ Paramètre text={'format': {'type': 'text'}, 'verbosity': 'medium'}")
        print("  ✅ tool_choice='none'")
        print("  ❌ PAS de paramètre reasoning")
        print("  ✅ Instructions claires avec demande explicite de réponse")
    else:
        print("\n⚠️ Même la configuration qui marche a échoué...")

if __name__ == "__main__":
    main()
