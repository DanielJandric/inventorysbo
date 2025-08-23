#!/usr/bin/env python3
"""Test rapide des corrections IA"""
import sys
import json
import types

def setup_mocks():
    # Mock openai with proper structure
    fake_openai = types.ModuleType("openai")
    
    class FakeChoice:
        def __init__(self, content):
            self.message = types.SimpleNamespace(content=content)
    
    class FakeResponse:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]
    
    class FakeCompletions:
        def create(self, **kwargs):
            # Simulate different responses based on model
            if "json" in str(kwargs.get("messages", [])).lower():
                return FakeResponse('{"estimated_price": 45000, "reasoning": "Test reasoning", "confidence_score": 0.8, "market_trend": "stable"}')
            else:
                return FakeResponse("Réponse IA pour chatbot - Collection analysée avec succès")
    
    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()
    
    class FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = FakeChat()
    
    fake_openai.OpenAI = FakeOpenAI
    sys.modules["openai"] = fake_openai
    
    # Mock gpt5_compat
    gpt5_stub = types.ModuleType("gpt5_compat")
    
    def fake_from_responses_simple(**kwargs):
        return types.SimpleNamespace()
    
    def fake_extract_output_text(resp):
        return '{"estimated_price": 45000, "reasoning": "Test reasoning via gpt5_compat", "confidence_score": 0.8, "market_trend": "stable"}'
    
    gpt5_stub.from_responses_simple = fake_from_responses_simple
    gpt5_stub.extract_output_text = fake_extract_output_text
    sys.modules["gpt5_compat"] = gpt5_stub
    
    # Mock supabase
    fake_supabase_module = types.ModuleType("supabase")
    fake_items = [
        {"id": 1, "name": "Test Rolex", "category": "Montres", "current_value": 15000, "construction_year": 2020},
        {"id": 2, "name": "Test Porsche", "category": "Voitures", "current_value": 85000, "construction_year": 2018}
    ]
    
    fake_table = types.SimpleNamespace(
        select=lambda *a, **k: types.SimpleNamespace(
            eq=lambda col, val: types.SimpleNamespace(
                execute=lambda: types.SimpleNamespace(data=[item for item in fake_items if item["id"] == val])
            ),
            execute=lambda: types.SimpleNamespace(data=fake_items)
        ),
        update=lambda data: types.SimpleNamespace(
            eq=lambda col, val: types.SimpleNamespace(
                execute=lambda: types.SimpleNamespace(data=[{**item, **data} for item in fake_items if item["id"] == val])
            )
        )
    )
    
    fake_supabase_module.create_client = lambda *a, **k: types.SimpleNamespace(
        table=lambda name: fake_table
    )
    sys.modules["supabase"] = fake_supabase_module
    
    # Mock other deps
    ws_stub = types.ModuleType("web_search_manager")
    ws_stub.create_web_search_manager = lambda *a, **k: None
    sys.modules["web_search_manager"] = ws_stub
    
    ma_stub = types.ModuleType("market_analysis_db")
    ma_stub.get_market_analysis_db = lambda: types.SimpleNamespace(save_analysis=lambda x: 456)
    ma_stub.MarketAnalysis = lambda **kwargs: types.SimpleNamespace(**kwargs)
    sys.modules["market_analysis_db"] = ma_stub

def test_ia_fixes():
    import os
    os.environ.update({
        "SUPABASE_URL": "http://localhost",
        "SUPABASE_KEY": "test-key", 
        "OPENAI_API_KEY": "sk-test",
        "AI_MODEL": "gpt-4-turbo-preview"
    })
    
    try:
        setup_mocks()
        
        import app
        flask_app = app.app
        flask_app.testing = True
        
        with flask_app.test_client() as client:
            print("🔧 Test des corrections IA")
            
            # Test 1: Chatbot amélioré avec contexte collection
            payload = {"message": "Quelle est la valeur totale de ma collection?", "session_id": "test123"}
            resp = client.post("/api/chatbot", 
                             data=json.dumps(payload), 
                             content_type="application/json")
            print(f"💬 Chatbot avec contexte: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.get_json()
                print(f"   Reply: {data['reply'][:80]}...")
                print(f"   Items count: {data['metadata'].get('items_count')}")
                print("   ✅ Chatbot avec contexte collection fonctionne!")
            
            # Test 2: Prix IA avec parsing JSON robuste
            resp = client.post("/api/ai-update-price/1")
            print(f"💰 Prix IA robuste: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.get_json()
                print(f"   Prix estimé: {data.get('estimated_price')} CHF")
                print(f"   Reasoning: {data.get('reasoning', 'N/A')[:50]}...")
                print(f"   Confidence: {data.get('confidence_score')}")
                print("   ✅ Prix IA avec JSON parsing fonctionne!")
            elif resp.status_code == 400:
                data = resp.get_json()
                print(f"   Erreur JSON: {data.get('error', 'Unknown')}")
            
            # Test 3: Worker background
            payload = {"prompt": "Test analysis improved"}
            resp = client.post("/api/background-worker/trigger",
                             data=json.dumps(payload),
                             content_type="application/json")
            print(f"⚙️ Background worker: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.get_json()
                print(f"   Analysis ID: {data.get('analysis_id')}")
                print("   ✅ Background worker fonctionne!")
                
            print("\n🎉 Tests des corrections IA terminés!")
            return True
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ia_fixes()
    exit(0 if success else 1)
