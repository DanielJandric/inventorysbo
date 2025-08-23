# test_simple_responses.py
import os
from openai import OpenAI

client = OpenAI()

def test_simple_responses():
    """Test simple de l'API Responses sans paramètres complexes."""
    
    prompt = "Quelles sont les tendances actuelles du marché immobilier ?"
    
    print("🎯 TEST SIMPLE: RESPONSES API SANS PARAMÈTRES COMPLEXES\n")
    print("=" * 60)
    
    # Test 1: Configuration minimale avec instructions claires
    print("\n📋 TEST 1: Configuration minimale")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
        # Explorer la structure de la réponse
        print(f"\n🔍 STRUCTURE DE LA RÉPONSE:")
        print(f"  - Tous les attributs: {[attr for attr in dir(res) if not attr.startswith('_')]}")
        
        if hasattr(res, 'output') and res.output:
            print(f"\n📦 OUTPUT DÉTAILLÉ:")
            for i, item in enumerate(res.output):
                print(f"  Item {i}:")
                print(f"    - Type: {getattr(item, 'type', 'N/A')}")
                print(f"    - ID: {getattr(item, 'id', 'N/A')}")
                print(f"    - Summary: {getattr(item, 'summary', 'N/A')}")
                print(f"    - Content: {getattr(item, 'content', 'N/A')}")
                print(f"    - Status: {getattr(item, 'status', 'N/A')}")
                print(f"    - Tous les attributs: {[attr for attr in dir(item) if not attr.startswith('_')]}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Essayer d'accéder au contenu via différentes méthodes
    print("\n📋 TEST 2: Extraction du contenu")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Tu DOIS émettre une réponse finale en français. Commence par 'OK –'",
            input=prompt,
            max_output_tokens=200
        )
        
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        
        # Essayer toutes les méthodes d'extraction possibles
        print(f"\n🔍 MÉTHODES D'EXTRACTION:")
        print(f"  - res.output_text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"  - res.text: {getattr(res, 'text', 'N/A')}")
        print(f"  - res.content: {getattr(res, 'content', 'N/A')}")
        print(f"  - res.response: {getattr(res, 'response', 'N/A')}")
        print(f"  - res.message: {getattr(res, 'message', 'N/A')}")
        
        # Essayer de convertir en dict pour voir tout le contenu
        try:
            res_dict = res.model_dump()
            print(f"\n📋 CONTENU COMPLET (model_dump):")
            print(f"  - Keys: {list(res_dict.keys())}")
            for key, value in res_dict.items():
                if key in ['output', 'reasoning', 'usage']:
                    print(f"  - {key}: {value}")
        except Exception as e:
            print(f"  - Erreur model_dump: {e}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Veuillez définir OPENAI_API_KEY.", file=sys.stderr)
        exit(1)
    
    test_simple_responses()
