# test_summary_activation.py
import os
from openai import OpenAI

client = OpenAI()

def test_summary_activation():
    """Test pour essayer d'activer le champ summary de l'API Responses."""
    
    prompt = "Quelles sont les tendances actuelles du marché immobilier ?"
    
    print("🧠 TEST: ACTIVATION DU CHAMP SUMMARY\n")
    print("=" * 50)
    
    # Test 1: Essayer avec reasoning.summary=True
    print("\n📋 TEST 1: reasoning.summary=True")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            reasoning={"effort": "high", "summary": True},
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
        if hasattr(res, 'reasoning') and res.reasoning:
            print(f"\n🧠 REASONING:")
            print(f"  - Effort: {getattr(res.reasoning, 'effort', 'N/A')}")
            print(f"  - Summary: {getattr(res.reasoning, 'summary', 'N/A')}")
        
        if hasattr(res, 'output') and res.output:
            output_item = res.output[0]
            print(f"\n📦 OUTPUT[0]:")
            print(f"  - Type: {getattr(output_item, 'type', 'N/A')}")
            print(f"  - Summary: {getattr(output_item, 'summary', 'N/A')}")
            print(f"  - Content: {getattr(output_item, 'content', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Essayer avec reasoning.summary="detailed"
    print("\n📋 TEST 2: reasoning.summary='detailed'")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            reasoning={"effort": "high", "summary": "detailed"},
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        
        if hasattr(res, 'output') and res.output:
            output_item = res.output[0]
            print(f"\n📦 OUTPUT[0]:")
            print(f"  - Type: {getattr(output_item, 'type', 'N/A')}")
            print(f"  - Summary: {getattr(output_item, 'summary', 'N/A')}")
            print(f"  - Content: {getattr(output_item, 'content', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Essayer avec reasoning.summary="concise"
    print("\n📋 TEST 3: reasoning.summary='concise'")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            reasoning={"effort": "high", "summary": "concise"},
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        
        if hasattr(res, 'output') and res.output:
            output_item = res.output[0]
            print(f"\n📦 OUTPUT[0]:")
            print(f"  - Type: {getattr(output_item, 'type', 'N/A')}")
            print(f"  - Summary: {getattr(output_item, 'summary', 'N/A')}")
            print(f"  - Content: {getattr(output_item, 'content', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 4: Essayer avec reasoning.summary="auto"
    print("\n📋 TEST 4: reasoning.summary='auto'")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            reasoning={"effort": "high", "summary": "auto"},
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        
        if hasattr(res, 'output') and res.output:
            output_item = res.output[0]
            print(f"\n📦 OUTPUT[0]:")
            print(f"  - Type: {getattr(output_item, 'type', 'N/A')}")
            print(f"  - Summary: {getattr(output_item, 'summary', 'N/A')}")
            print(f"  - Content: {getattr(output_item, 'content', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 5: Essayer avec un prompt très directif pour forcer la sortie
    print("\n📋 TEST 5: Prompt très directif")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt + "\n\nIMPORTANT: Tu DOIS écrire ta réponse maintenant. Pas de raisonnement interne, juste la réponse finale.",
            reasoning={"effort": "high", "summary": "detailed"},
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        
        if hasattr(res, 'output') and res.output:
            output_item = res.output[0]
            print(f"\n📦 OUTPUT[0]:")
            print(f"  - Type: {getattr(output_item, 'type', 'N/A')}")
            print(f"  - Summary: {getattr(output_item, 'summary', 'N/A')}")
            print(f"  - Content: {getattr(output_item, 'content', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Veuillez définir OPENAI_API_KEY.", file=sys.stderr)
        exit(1)
    
    test_summary_activation()
