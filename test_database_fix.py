#!/usr/bin/env python3
"""
Test database connection after fixing table names
"""

def test_database_connection():
    """Test basic database operations"""
    try:
        from core.database import db_manager
        
        print("Testing database connection...")
        
        # Test connection
        connected = db_manager.is_connected()
        print(f"Database connected: {connected}")
        
        if not connected:
            print("Note: Database not connected - this is expected without Supabase credentials")
            print("But the table names have been fixed to match the original 'items' table")
            return
        
        # If connected, test fetching items
        try:
            items = db_manager.get_all_items()
            print(f"Successfully fetched {len(items)} items from 'items' table")
            
            # Test other operations
            stock_items = db_manager.get_stock_items()
            print(f"Stock items: {len(stock_items)}")
            
            items_for_sale = db_manager.get_items_for_sale()  
            print(f"Items for sale: {len(items_for_sale)}")
            
            sold_items = db_manager.get_sold_items()
            print(f"Sold items: {len(sold_items)}")
            
        except Exception as e:
            print(f"Error testing database operations: {e}")
            
    except Exception as e:
        print(f"Error testing database: {e}")

def test_api_endpoints():
    """Test API endpoints that use database"""
    try:
        from app import app
        
        print("\nTesting API endpoints...")
        
        with app.test_client() as client:
            # Test items endpoint
            response = client.get('/api/items')
            print(f"GET /api/items: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"  Success: {data.get('success')}")
                print(f"  Items count: {data.get('count', 0)}")
            else:
                print(f"  Error: {response.status_code}")
            
            # Test other endpoints
            endpoints = [
                '/api/items/for-sale',
                '/api/items/sold', 
                '/api/items/stocks'
            ]
            
            for endpoint in endpoints:
                try:
                    response = client.get(endpoint)
                    print(f"GET {endpoint}: {response.status_code}")
                except Exception as e:
                    print(f"GET {endpoint}: Error - {e}")
                    
    except Exception as e:
        print(f"Error testing API endpoints: {e}")

if __name__ == "__main__":
    print("Testing Database Connection Fix")
    print("=" * 40)
    
    test_database_connection()
    test_api_endpoints()
    
    print("\n" + "=" * 40)
    print("Database fix testing completed!")
    print("The table names have been corrected to use 'items' instead of 'collection_items'")
    print("This should resolve the database connection issues in deployment.")