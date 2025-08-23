# test_reasoning_content.py
import os
from openai import OpenAI

client = OpenAI()

def test_reasoning_content():
    """Test pour explorer le contenu du champ reasoning."""
    
    prompt = "Quelles sont les tendances actuelles du marché immobilier ?"
    
    print("🧠 TEST: EXPLORER LE CONTENU DU REASONING\n")
    print("=" * 50)
    
    # Test 1: Explorer le contenu du reasoning
    print("\n📋 TEST 1: Explorer le reasoning")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            text={"format": {"type": "text"}, "verbosity": "high"},
            tool_choice="none",
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
        # Explorer le contenu du reasoning
        if hasattr(res, 'reasoning') and res.reasoning:
            print(f"\n🧠 REASONING DÉTAILLÉ:")
            print(f"  - Effort: {getattr(res.reasoning, 'effort', 'N/A')}")
            print(f"  - Generate summary: {getattr(res.reasoning, 'generate_summary', 'N/A')}")
            print(f"  - Summary: {getattr(res.reasoning, 'summary', 'N/A')}")
            
            # Essayer d'accéder aux attributs du reasoning
            print(f"  - Tous les attributs: {[attr for attr in dir(res.reasoning) if not attr.startswith('_')]}")
        
        # Explorer le contenu de output[0]
        if hasattr(res, 'output') and res.output:
            print(f"\n📦 OUTPUT[0] DÉTAILLÉ:")
            output_item = res.output[0]
            print(f"  - Type: {getattr(output_item, 'type', 'N/A')}")
            print(f"  - Summary: {getattr(output_item, 'summary', 'N/A')}")
            print(f"  - Content: {getattr(output_item, 'content', 'N/A')}")
            print(f"  - Status: {getattr(output_item, 'status', 'N/A')}")
            print(f"  - Tous les attributs: {[attr for attr in dir(output_item) if not attr.startswith('_')]}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Essayer de forcer la génération de summary
    print("\n📋 TEST 2: Forcer la génération de summary")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            text={"format": {"type": "text"}, "verbosity": "high"},
            tool_choice="none",
            reasoning={"effort": "high", "generate_summary": True},
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

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Veuillez définir OPENAI_API_KEY.", file=sys.stderr)
        exit(1)
    
    test_reasoning_content()
