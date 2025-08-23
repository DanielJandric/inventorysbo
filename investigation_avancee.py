# investigation_avancee.py
import os
from openai import OpenAI

client = OpenAI()

def investigation_avancee():
    """Investigation avancée de l'API Responses avec différentes approches."""
    
    prompt = "Quelles sont les tendances actuelles du marché immobilier ?"
    
    print("🔬 INVESTIGATION AVANCÉE DE L'API RESPONSES\n")
    print("=" * 60)
    
    # Test 1: Essayer avec un format différent
    print("\n📋 TEST 1: Format JSON au lieu de text")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en JSON avec clés 'points' et 'conclusion'.",
            input=prompt,
            text={"format": {"type": "json"}, "verbosity": "high"},
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Essayer sans paramètre text du tout
    print("\n📋 TEST 2: Sans paramètre text")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Essayer avec un modèle différent
    print("\n📋 TEST 3: Modèle gpt-5-2025-08-07")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5-2025-08-07",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            max_output_tokens=200
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 4: Essayer avec un prompt très simple
    print("\n📋 TEST 4: Prompt très simple")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            input="Dis-moi bonjour",
            max_output_tokens=50
        )
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        print(f"📝 Output text: '{getattr(res, 'output_text', 'N/A')}'")
        print(f"📦 Output: {getattr(res, 'output', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 5: Explorer la structure complète de la réponse
    print("\n📋 TEST 5: Structure complète de la réponse")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            max_output_tokens=200
        )
        
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        
        # Explorer tous les attributs de la réponse
        print(f"\n🔍 ATTRIBUTS COMPLETS:")
        for attr in dir(res):
            if not attr.startswith('_'):
                try:
                    value = getattr(res, attr)
                    if attr in ['output', 'reasoning', 'usage', 'text']:
                        print(f"  - {attr}: {value}")
                except Exception as e:
                    print(f"  - {attr}: Erreur d'accès - {e}")
        
        # Explorer le contenu de output[0] en détail
        if hasattr(res, 'output') and res.output:
            print(f"\n📦 OUTPUT[0] DÉTAILLÉ:")
            output_item = res.output[0]
            
            # Essayer d'accéder à tous les attributs
            for attr in dir(output_item):
                if not attr.startswith('_'):
                    try:
                        value = getattr(output_item, attr)
                        print(f"    - {attr}: {value}")
                    except Exception as e:
                        print(f"    - {attr}: Erreur d'accès - {e}")
            
            # Essayer de convertir en dict
            try:
                output_dict = output_item.model_dump()
                print(f"\n📋 OUTPUT[0] EN DICT:")
                for key, value in output_dict.items():
                    print(f"    - {key}: {value}")
            except Exception as e:
                print(f"    - Erreur model_dump: {e}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 6: Essayer d'accéder au contenu via différentes méthodes
    print("\n📋 TEST 6: Méthodes d'extraction alternatives")
    print("-" * 40)
    try:
        res = client.responses.create(
            model="gpt-5",
            instructions="Tu es un analyste marchés. Réponds en français.",
            input=prompt,
            max_output_tokens=200
        )
        
        print(f"✅ Succès - Status: {getattr(res, 'status', 'N/A')}")
        
        # Essayer toutes les méthodes d'extraction possibles
        print(f"\n🔍 MÉTHODES D'EXTRACTION:")
        
        # Méthodes directes
        methods = ['output_text', 'text', 'content', 'response', 'message', 'answer', 'result']
        for method in methods:
            try:
                value = getattr(res, method, 'N/A')
                print(f"  - res.{method}: {value}")
            except Exception as e:
                print(f"  - res.{method}: Erreur - {e}")
        
        # Essayer d'accéder au contenu via output
        if hasattr(res, 'output') and res.output:
            print(f"\n📦 EXTRACTION VIA OUTPUT:")
            for i, item in enumerate(res.output):
                print(f"  Item {i}:")
                
                # Essayer d'accéder au contenu de différentes manières
                if hasattr(item, 'content') and item.content:
                    print(f"    - Content: {item.content}")
                if hasattr(item, 'text') and item.text:
                    print(f"    - Text: {item.text}")
                if hasattr(item, 'message') and item.message:
                    print(f"    - Message: {item.message}")
                if hasattr(item, 'response') and item.response:
                    print(f"    - Response: {item.response}")
                
                # Essayer de convertir en dict
                try:
                    item_dict = item.model_dump()
                    print(f"    - Dict keys: {list(item_dict.keys())}")
                    for key, value in item_dict.items():
                        if value and key not in ['id', 'type', 'status']:
                            print(f"      {key}: {value}")
                except Exception as e:
                    print(f"    - Erreur model_dump: {e}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Veuillez définir OPENAI_API_KEY.", file=sys.stderr)
        exit(1)
    
    investigation_avancee()
