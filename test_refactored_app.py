#!/usr/bin/env python3
"""
Test script for the refactored application.
"""

def test_stock_price():
    """Test stock price functionality"""
    try:
        from services.market_service import market_service
        print("Testing stock price for AAPL...")
        
        result = market_service.get_stock_price('AAPL')
        
        if result:
            print(f"Success! Price: {result.get('price')} {result.get('currency')}")
            print(f"   Change: {result.get('change_percent', 'N/A')}%")
            print(f"   Source: {result.get('source')}")
        else:
            print("Failed to get stock price")
            
    except Exception as e:
        print(f"Error testing stock price: {e}")

def test_market_briefing():
    """Test market briefing functionality"""
    try:
        from services.market_service import market_service
        print("\nTesting market briefing...")
        
        result = market_service.get_market_briefing()
        
        if result:
            print("Market briefing generated successfully")
            print(f"   Summary length: {len(result.get('summary', ''))}")
            print(f"   Indices count: {len(result.get('indices', []))}")
        else:
            print("Failed to get market briefing")
            
    except Exception as e:
        print(f"Error testing market briefing: {e}")

def test_ai_service():
    """Test AI service"""
    try:
        from services.ai_service import ai_service
        print("\nTesting AI service...")
        
        available = ai_service.is_available()
        print(f"AI service available: {available}")
        
        if available:
            # Test embedding generation
            embedding = ai_service.generate_embedding("test message")
            if embedding:
                print(f"   Embedding generated: {len(embedding)} dimensions")
            
    except Exception as e:
        print(f"Error testing AI service: {e}")

def test_database():
    """Test database connection"""
    try:
        from core.database import db_manager
        print("\nTesting database connection...")
        
        connected = db_manager.is_connected()
        print(f"Database connected: {connected}")
        
        if not connected:
            print("   Note: Database not configured (expected in test environment)")
        
    except Exception as e:
        print(f"Error testing database: {e}")

def test_flask_routes():
    """Test Flask application routes"""
    try:
        from app import app
        print(f"\nTesting Flask application...")
        print(f"App created successfully")
        print(f"   Routes count: {len(list(app.url_map.iter_rules()))}")
        
        # List some key routes
        key_routes = []
        for rule in app.url_map.iter_rules():
            if any(path in rule.rule for path in ['/api/items', '/api/chatbot', '/api/stock-price']):
                key_routes.append(f"   {rule.rule} ({rule.methods - {'HEAD', 'OPTIONS'}})")
        
        print("Key API routes:")
        for route in key_routes[:10]:
            print(route)
        
    except Exception as e:
        print(f"Error testing Flask routes: {e}")

if __name__ == "__main__":
    print("Testing Refactored Inventory SBO Application\n")
    print("=" * 50)
    
    test_flask_routes()
    test_stock_price()
    test_market_briefing()
    test_ai_service()
    test_database()
    
    print("\n" + "=" * 50)
    print("Testing completed!")