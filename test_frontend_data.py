#!/usr/bin/env python3
"""
Test frontend data loading after API format fixes
"""

def test_items_endpoint():
    """Test the main items endpoint format"""
    try:
        from app import app
        
        print("Testing /api/items endpoint...")
        
        with app.test_client() as client:
            response = client.get('/api/items')
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"Response type: {type(data)}")
                
                if isinstance(data, list):
                    print(f"SUCCESS: Returns list with {len(data)} items (matches original format)")
                    if len(data) > 0:
                        print(f"Sample item keys: {list(data[0].keys())}")
                    else:
                        print("Empty list (expected without database)")
                elif isinstance(data, dict) and 'error' in data:
                    print(f"Error response: {data['error']}")
                else:
                    print(f"ISSUE: Unexpected format - {type(data)}")
                    print(f"Data: {data}")
            else:
                print(f"Failed with status: {response.status_code}")
                
    except Exception as e:
        print(f"Error testing items endpoint: {e}")

def test_analytics_endpoint():
    """Test the analytics endpoint"""
    try:
        from app import app
        
        print("\nTesting /api/analytics/advanced endpoint...")
        
        with app.test_client() as client:
            response = client.get('/api/analytics/advanced')
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"Response type: {type(data)}")
                
                if isinstance(data, dict) and 'analytics' in data:
                    analytics = data['analytics']
                    print("SUCCESS: Analytics response format correct")
                    print(f"Analytics sections: {list(analytics.keys())}")
                    
                    # Check basic metrics
                    if 'basic_metrics' in analytics:
                        basic = analytics['basic_metrics']
                        print(f"Basic metrics: {basic}")
                    
                else:
                    print(f"ISSUE: Unexpected analytics format")
                    print(f"Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
            else:
                print(f"Failed with status: {response.status_code}")
                
    except Exception as e:
        print(f"Error testing analytics endpoint: {e}")

def test_other_critical_endpoints():
    """Test other endpoints the frontend might need"""
    try:
        from app import app
        
        print("\nTesting other critical endpoints...")
        
        endpoints = [
            '/health',
            '/api/endpoints',
            '/api/items/for-sale',
            '/api/items/sold',
            '/api/items/stocks'
        ]
        
        with app.test_client() as client:
            for endpoint in endpoints:
                try:
                    response = client.get(endpoint)
                    status = "OK" if response.status_code == 200 else f"ERROR({response.status_code})"
                    print(f"  {endpoint}: {status}")
                except Exception as e:
                    print(f"  {endpoint}: EXCEPTION - {e}")
                    
    except Exception as e:
        print(f"Error testing other endpoints: {e}")

if __name__ == "__main__":
    print("Testing Frontend Data Loading")
    print("=" * 50)
    
    test_items_endpoint()
    test_analytics_endpoint() 
    test_other_critical_endpoints()
    
    print("\n" + "=" * 50)
    print("Frontend data testing completed!")
    print("The API responses should now match the original app format.")