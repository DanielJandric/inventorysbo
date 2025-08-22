# test_no_reasoning.py
import os
from openai import OpenAI

client = OpenAI()

def test_no_reasoning():
    """Test pour désactiver le reasoning et forcer la sortie text."""
    
    prompt = "Quelles sont les tendances actuelles du marché immobilier ?"
    
    print("🧠 TEST: DÉSACTIVER LE REASONING\n")
    print("=" * 50)
    
    # Test 1: Essayer de désactiver le reasoning
    print("\n📋 TEST 1: Désactiver le reasoning")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            text={"format": {"type": "text"}, "verbosity": "high"},
            max_output_tokens=200,
            # Essayer de désactiver le reasoning
            reasoning=None
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        print(f"🧠 Reasoning: {getattr(res, 'reasoning', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Essayer avec tool_choice="none" et pas de reasoning
    print("\n📋 TEST 2: tool_choice='none' sans reasoning")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            text={"format": {"type": "text"}, "verbosity": "high"},
            tool_choice="none",
            max_output_tokens=200
            # Pas de paramètre reasoning
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        print(f"🧠 Reasoning: {getattr(res, 'reasoning', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Essayer avec un prompt très directif
    print("\n📋 TEST 3: Prompt très directif")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt + "\n\nIMPORTANT: Tu DOIS écrire ta réponse maintenant. Pas de raisonnement interne, juste la réponse finale.",
            text={"format": {"type": "text"}, "verbosity": "high"},
            tool_choice="none",
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        print(f"🧠 Reasoning: {getattr(res, 'reasoning', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Veuillez définir OPENAI_API_KEY.", file=sys.stderr)
        exit(1)
    
    test_no_reasoning()
