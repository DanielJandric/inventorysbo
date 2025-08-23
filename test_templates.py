#!/usr/bin/env python3
"""
Test template routes after fixing names
"""

def test_main_route():
    try:
        from app import app
        
        with app.test_client() as client:
            response = client.get('/')
            print(f"Main route status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Main route working correctly!")
            else:
                print(f"❌ Main route failed with status {response.status_code}")
                
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error testing main route: {e}")
        return False

def test_other_routes():
    try:
        from app import app
        
        routes_to_test = [
            '/analytics',
            '/reports', 
            '/markets',
            '/settings',
            '/sold',
            '/real-estate'
        ]
        
        with app.test_client() as client:
            for route in routes_to_test:
                try:
                    response = client.get(route)
                    status = "✅" if response.status_code == 200 else "❌"
                    print(f"{status} {route}: {response.status_code}")
                except Exception as e:
                    print(f"❌ {route}: Error - {e}")
                    
    except Exception as e:
        print(f"❌ Error testing routes: {e}")

if __name__ == "__main__":
    print("Testing template routes...")
    print("=" * 40)
    
    success = test_main_route()
    print()
    test_other_routes()
    
    print()
    print("=" * 40)
    if success:
        print("✅ Template fix appears successful!")
    else:
        print("❌ Main route still has issues")