# debug_responses_api.py
import os, json, sys
from openai import OpenAI, OpenAIError

client = OpenAI()

def debug_responses_api():
    """Diagnostic complet de l'API Responses avec différents paramètres."""
    
    prompt = "Quelles sont les tendances actuelles du marché immobilier ?"
    
    print("🔍 DIAGNOSTIC COMPLET DE L'API RESPONSES\n")
    print("=" * 60)
    
    # Test 1: Configuration minimale
    print("\n📋 TEST 1: Configuration minimale")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            input=prompt,
            max_output_tokens=100
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📊 Usage: {getattr(res, 'usage', 'N/A')}")
        print(f"🔑 Request ID: {getattr(res, '_request_id', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        print(f"📋 Instructions: {getattr(res, 'instructions', 'N/A')}")
        print(f"🎯 Tool choice: {getattr(res, 'tool_choice', 'N/A')}")
        print(f"🔧 Text config: {getattr(res, 'text', 'N/A')}")
        
        # Afficher tous les attributs disponibles
        print(f"\n📋 Tous les attributs: {[attr for attr in dir(res) if not attr.startswith('_')]}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Avec instructions
    print("\n📋 TEST 2: Avec instructions")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            max_output_tokens=100
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Avec configuration text
    print("\n📋 TEST 3: Avec configuration text")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            text={"format": {"type": "text"}},
            max_output_tokens=100
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 4: Avec verbosity
    print("\n📋 TEST 4: Avec verbosity")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            text={"format": {"type": "text"}, "verbosity": "high"},
            max_output_tokens=100
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 5: Sans text config
    print("\n📋 TEST 5: Sans configuration text")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            max_output_tokens=100
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 6: Avec reasoning
    print("\n📋 TEST 6: Avec reasoning")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            reasoning={"effort": "low"},
            max_output_tokens=100
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
        sys.exit(1)
    
    try:
        debug_responses_api()
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        sys.exit(1)
