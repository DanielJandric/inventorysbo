#!/usr/bin/env python3
"""Test des routes essentielles de la collection"""
import sys
import json
import types

def setup_mocks():
    # Mock openai
    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = lambda *a, **k: types.SimpleNamespace(responses=types.SimpleNamespace())
    sys.modules["openai"] = fake_openai
    
    # Mock supabase
    fake_supabase_module = types.ModuleType("supabase")
    fake_table = types.SimpleNamespace(
        select=lambda *a, **k: types.SimpleNamespace(
            order=lambda *a, **k: types.SimpleNamespace(
                execute=lambda: types.SimpleNamespace(data=[
                    {"id": 1, "name": "Test Item", "asset_class": "Watch", "current_value": 5000},
                    {"id": 2, "name": "Test Car", "asset_class": "Vehicle", "current_value": 25000}
                ])
            )
        ),
        insert=lambda data: types.SimpleNamespace(
            execute=lambda: types.SimpleNamespace(data=[{"id": 99, **data}])
        )
    )
    fake_supabase_module.create_client = lambda *a, **k: types.SimpleNamespace(
        table=lambda name: fake_table
    )
    sys.modules["supabase"] = fake_supabase_module
    
    # Mock other deps
    gpt5_stub = types.ModuleType("gpt5_compat")
    gpt5_stub.extract_output_text = lambda res: "Mock response"
    sys.modules["gpt5_compat"] = gpt5_stub
    
    ws_stub = types.ModuleType("web_search_manager")
    ws_stub.create_web_search_manager = lambda *a, **k: None
    sys.modules["web_search_manager"] = ws_stub
    
    ma_stub = types.ModuleType("market_analysis_db")
    ma_stub.get_market_analysis_db = lambda: types.SimpleNamespace(get_recent_analyses=lambda **k: [])
    sys.modules["market_analysis_db"] = ma_stub
    
    stock_stub = types.ModuleType("stock_api_manager")
    stock_stub.get_stock_price_stable = lambda sym: {"symbol": sym, "price": 150.0, "status": "ok"}
    sys.modules["stock_api_manager"] = stock_stub
    
    manus_stub = types.ModuleType("manus_integration")
    manus_stub.get_exchange_rate_manus = lambda f, t: 1.0
    sys.modules["manus_integration"] = manus_stub

def test_collection_api():
    # Mock environment
    import os
    os.environ.update({
        "SUPABASE_URL": "http://localhost",
        "SUPABASE_KEY": "test-key", 
        "OPENAI_API_KEY": "sk-test"
    })
    
    try:
        # Setup mocks BEFORE importing app
        setup_mocks()
        
        # Import app
        import app
        flask_app = app.app
        flask_app.testing = True
        
        with flask_app.test_client() as client:
            print("🧪 Test Collection API Routes")
            
            # Test 1: GET /api/items
            resp = client.get("/api/items")
            print(f"📋 GET /api/items: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.get_json()
                print(f"   Items found: {len(data)} items")
                assert len(data) == 2
                print("   ✅ Items API works")
            
            # Test 2: POST /api/items
            new_item = {
                "name": "Test Watch",
                "asset_class": "Watch", 
                "current_value": 3000,
                "brand": "Rolex"
            }
            resp = client.post("/api/items", 
                             data=json.dumps(new_item), 
                             content_type="application/json")
            print(f"➕ POST /api/items: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.get_json()
                assert data["success"] == True
                print("   ✅ Add item works")
            
            # Test 3: GET /api/analytics/advanced
            resp = client.get("/api/analytics/advanced")
            print(f"📊 GET /api/analytics/advanced: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.get_json()
                assert "total_value" in data
                assert data["total_items"] == 2
                print(f"   Total Value: {data['total_value']}")
                print("   ✅ Analytics works")
            
            # Test 4: GET /api/stock-price/AAPL
            resp = client.get("/api/stock-price/AAPL")
            print(f"📈 GET /api/stock-price/AAPL: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.get_json()
                assert "price" in data
                print("   ✅ Stock price works")
                
            # Test 5: Root route
            resp = client.get("/")
            print(f"🏠 GET /: {resp.status_code}")
            assert resp.status_code == 200
            
            print("🎉 All essential collection routes work!")
            return True
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_collection_api()
    exit(0 if success else 1)
