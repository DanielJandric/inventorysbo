#!/usr/bin/env python3
"""Test rapide du nouveau app.py (anciennement app_refactored.py)"""
import sys
import json
import types

def _make_fake_openai_class(captured):
    counter = {"n": 0}

    class _FakeResponse:
        def __init__(self, rid: str):
            self.id = rid
            self.output_text = "✅ GPT-5 Ready for Render Deployment"

    class _FakeResponses:
        def create(self, **kwargs):
            captured.append(kwargs)
            counter["n"] += 1
            return _FakeResponse(f"resp{counter['n']}")

    class _FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self._responses = _FakeResponses()
        def with_options(self, timeout=None):
            return self
        @property
        def responses(self):
            return self._responses

    return _FakeOpenAI

def test_final_app():
    # Mock dependencies
    captured = []
    
    # Stub openai
    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = _make_fake_openai_class(captured)
    sys.modules["openai"] = fake_openai
    
    # Stub supabase
    supabase_stub = types.ModuleType("supabase")
    supabase_stub.create_client = lambda *a, **k: types.SimpleNamespace(
        table=lambda name: types.SimpleNamespace(
            select=lambda *a, **k: types.SimpleNamespace(execute=lambda: types.SimpleNamespace(data=[]))
        )
    )
    sys.modules["supabase"] = supabase_stub
    
    # Stub other modules
    gpt5_stub = types.ModuleType("gpt5_compat")
    gpt5_stub.extract_output_text = lambda res: getattr(res, 'output_text', 'Response extracted')
    sys.modules["gpt5_compat"] = gpt5_stub
    
    ws_stub = types.ModuleType("web_search_manager")
    ws_stub.create_web_search_manager = lambda *a, **k: None
    ws_stub.WebSearchType = types.SimpleNamespace(MARKET_DATA="market_data")
    sys.modules["web_search_manager"] = ws_stub
    
    ma_stub = types.ModuleType("market_analysis_db")
    ma_stub.get_market_analysis_db = lambda: types.SimpleNamespace(get_recent_analyses=lambda **k: [])
    sys.modules["market_analysis_db"] = ma_stub
    
    # Set env vars
    import os
    os.environ.update({
        "SUPABASE_URL": "http://localhost",
        "SUPABASE_KEY": "test-key", 
        "OPENAI_API_KEY": "sk-test"
    })
    
    try:
        # Import the new app.py (was app_refactored.py)
        import app
        flask_app = app.app
        flask_app.testing = True
        
        with flask_app.test_client() as client:
            # Test markets endpoint
            resp = client.post("/api/markets/chat", 
                             data=json.dumps({"message": "Test deployment"}), 
                             content_type="application/json")
            
            print(f"🚀 Deployment Test - Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.get_json()
                print(f"✅ SUCCESS: {data.get('reply', 'No reply')}")
                print(f"📡 API called with: {list(captured[-1].keys()) if captured else 'No API call'}")
                return True
            else:
                print(f"❌ ERROR: {resp.get_json()}")
                return False
                
    except Exception as e:
        print(f"❌ Import/Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_final_app()
    exit(0 if success else 1)
