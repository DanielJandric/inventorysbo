# test_final_responses.py
import os
from openai import OpenAI

client = OpenAI()

def test_final_responses():
    """Test final avec la bonne configuration pour l'API Responses."""
    
    prompt = "Quelles sont les tendances actuelles du marché immobilier ?"
    
    print("🎯 TEST FINAL: CONFIGURATION OPTIMALE RESPONSES API\n")
    print("=" * 60)
    
    # Test 1: Avec generate_summary="concise"
    print("\n📋 TEST 1: generate_summary='concise'")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            text={"format": {"type": "text"}, "verbosity": "high"},
            tool_choice="none",
            reasoning={"effort": "high", "generate_summary": "concise"},
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
        if hasattr(res, 'reasoning') and res.reasoning:
            print(f"\n🧠 REASONING AVEC SUMMARY:")
            print(f"  - Effort: {getattr(res.reasoning, 'effort', 'N/A')}")
            print(f"  - Generate summary: {getattr(res.reasoning, 'generate_summary', 'N/A')}")
            print(f"  - Summary: {getattr(res.reasoning, 'summary', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Avec generate_summary="detailed"
    print("\n📋 TEST 2: generate_summary='detailed'")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            text={"format": {"type": "text"}, "verbosity": "high"},
            tool_choice="none",
            reasoning={"effort": "high", "generate_summary": "detailed"},
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
        if hasattr(res, 'reasoning') and res.reasoning:
            print(f"\n🧠 REASONING AVEC SUMMARY:")
            print(f"  - Summary: {getattr(res.reasoning, 'summary', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Essayer d'accéder au contenu via output[0].summary
    print("\n📋 TEST 3: Accéder au contenu via output[0].summary")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            text={"format": {"type": "text"}, "verbosity": "high"},
            tool_choice="none",
            reasoning={"effort": "high", "generate_summary": "detailed"},
            max_output_tokens=200
        )
        
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        
        # Essayer d'extraire le contenu de différentes manières
        if hasattr(res, 'output') and res.output:
            output_item = res.output[0]
            print(f"\n📦 CONTENU EXTRACTIBLE:")
            print(f"  - Type: {getattr(output_item, 'type', 'N/A')}")
            print(f"  - Summary: {getattr(output_item, 'summary', 'N/A')}")
            print(f"  - Content: {getattr(output_item, 'content', 'N/A')}")
            
            # Si summary contient du contenu, l'afficher
            if hasattr(output_item, 'summary') and output_item.summary:
                print(f"\n📝 CONTENU TROUVÉ DANS SUMMARY:")
                for i, item in enumerate(output_item.summary):
                    print(f"  {i+1}. {item}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Veuillez définir OPENAI_API_KEY.", file=sys.stderr)
        exit(1)
    
    test_final_responses()
