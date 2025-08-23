"""
Refactored Flask application for Inventory SBO.
This is a completely restructured version of the original app.py with modular architecture.
"""

import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_cors import CORS

# Core imports
from core.app_config import Config
from core.database import db_manager
from core.models import CollectionItem

# Service imports
from services.ai_service import ai_service
from services.email_service import email_service
from services.market_service import market_service

# Route blueprints
from routes.items import items_bp
from routes.ai import ai_bp
from routes.market import market_bp

# Import metrics blueprint
from metrics_api import metrics_bp

logger = logging.getLogger(__name__)


def calculate_advanced_analytics(items):
    """Calculate advanced analytics similar to original app"""
    from core.utils import is_item_available, is_item_sold
    
    # Basic metrics
    total = len(items)
    available = len([i for i in items if is_item_available(i)])
    sold = len([i for i in items if is_item_sold(i)])
    for_sale = len([i for i in items if getattr(i, 'for_sale', False)])
    
    total_value = sum((getattr(i, 'current_value', 0) or 0) for i in items if is_item_available(i))
    
    # Category analytics
    categories = {}
    for item in items:
        cat = getattr(item, 'category', 'Unknown')
        if cat not in categories:
            categories[cat] = {'count': 0, 'value': 0}
        categories[cat]['count'] += 1
        if is_item_available(item):
            categories[cat]['value'] += (getattr(item, 'current_value', 0) or 0)
    
    # Stock analytics
    stock_items = [i for i in items if getattr(i, 'stock_symbol', None)]
    stock_value = 0
    for item in stock_items:
        if hasattr(item, 'current_price') and hasattr(item, 'stock_quantity'):
            if item.current_price and item.stock_quantity:
                stock_value += float(item.current_price) * float(item.stock_quantity)
    
    return {
        'basic_metrics': {
            'total_items': total,
            'available_items': available,
            'sold_items': sold,
            'items_for_sale': for_sale,
            'total_value': total_value,
            'average_value': total_value / available if available > 0 else 0
        },
        'financial_metrics': {
            'total_portfolio_value': total_value + stock_value,
            'stock_portfolio_value': stock_value,
            'collection_value': total_value,
            'currency': 'CHF'
        },
        'category_analytics': categories,
        'stock_analytics': {
            'total_stocks': len(stock_items),
            'stock_value': stock_value,
            'stock_symbols': [getattr(i, 'stock_symbol', '') for i in stock_items]
        },
        'sales_pipeline': {
            'items_for_sale': for_sale,
            'sale_conversion_rate': (sold / (sold + for_sale)) * 100 if (sold + for_sale) > 0 else 0
        },
        'performance_kpis': {
            'total_items': total,
            'portfolio_diversity': len(categories),
            'completion_rate': 100.0  # Placeholder
        }
    }


def create_app():
    """Application factory pattern"""
    
    # Validate configuration first - but continue even if some services are unavailable
    config_valid = Config.validate()
    if not config_valid:
        logger.warning("Some configuration missing - continuing with limited functionality")
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "https://inventorysbo.onrender.com"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(items_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(metrics_bp)
    
    # Main routes
    @app.route("/")
    def index():
        """Main dashboard"""
        return render_template('index.html')
    
    @app.route("/analytics")
    def analytics():
        """Analytics page"""
        return render_template('analytics.html')
    
    @app.route("/reports")
    def reports():
        """Reports page"""
        return render_template('reports.html')
    
    @app.route("/markets")
    def markets():
        """Markets page"""
        return render_template('markets.html')
    
    @app.route("/settings")
    def settings():
        """Settings page"""
        return render_template('settings.html')
    
    @app.route("/sold")
    def sold():
        """Sold items page"""
        return render_template('sold.html')
    
    @app.route("/real-estate")
    def real_estate():
        """Real estate page"""
        return render_template('real_estate.html')
    
    @app.route("/web-search")
    def web_search():
        """Web search page"""
        return render_template('web-search.html')
    
    @app.route("/google-search")
    def google_search():
        """Google search page"""
        return render_template('google-search.html')
    
    @app.route("/unified-market")
    def unified_market():
        """Unified market page"""
        return render_template('unified-market.html')
    
    @app.route("/google-cse")
    def google_cse():
        """Google CSE page"""
        return render_template('google-cse.html')
    
    @app.route("/intelligent-scraper")
    def intelligent_scraper_ui():
        """Intelligent scraper UI"""
        return render_template('intelligent-scraper.html')
    
    @app.route("/scrapingbee-scraper")
    def scrapingbee_scraper():
        """ScrapingBee scraper UI"""
        return render_template('scrapingbee-scraper.html')
    
    # System routes
    @app.route("/health")
    def health():
        """Health check endpoint"""
        try:
            # Check database connection
            db_connected = db_manager.is_connected()
            
            # Check AI service
            ai_available = ai_service.is_available()
            
            # Check email service
            email_status = email_service.get_status()
            
            # Check market service
            market_status = market_service.get_cache_status()
            
            status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'database': 'connected' if db_connected else 'disconnected',
                    'ai': 'available' if ai_available else 'unavailable',
                    'email': 'enabled' if email_status['enabled'] else 'disabled',
                    'market': 'active' if market_status.get('yfinance_available', False) else 'inactive'
                },
                'version': '2.0.0-refactored'
            }
            
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    @app.route("/api/analytics/advanced")
    def advanced_analytics():
        """Advanced analytics - matches original app"""
        try:
            items_data = db_manager.get_all_items()
            items = [CollectionItem.from_dict(item) for item in items_data]
            
            # Calculate analytics similar to original app
            analytics = calculate_advanced_analytics(items)
            
            return jsonify({
                "analytics": analytics,
                "metadata": {
                    "items_analyzed": len(items),
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0.0-refactored"
                }
            })
        except Exception as e:
            logger.error(f"Error in advanced analytics: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/endpoints")
    def list_endpoints():
        """List all available API endpoints"""
        endpoints = []
        
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                methods = [method for method in rule.methods if method not in ('HEAD', 'OPTIONS')]
                endpoints.append({
                    'endpoint': rule.rule,
                    'methods': methods,
                    'function': rule.endpoint
                })
        
        return jsonify({
            'success': True,
            'endpoints': sorted(endpoints, key=lambda x: x['endpoint']),
            'count': len(endpoints)
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'success': False,
            'error': 'Endpoint not found',
            'code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 500
        }), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors"""
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'code': 403
        }), 403
    
    # Service status endpoints
    @app.route("/api/status/services")
    def service_status():
        """Get status of all services"""
        return jsonify({
            'success': True,
            'services': {
                'database': {
                    'connected': db_manager.is_connected(),
                    'url_configured': bool(Config.SUPABASE_URL)
                },
                'ai': {
                    'available': ai_service.is_available(),
                    'key_configured': bool(Config.OPENAI_API_KEY)
                },
                'email': email_service.get_status(),
                'market': market_service.get_cache_status()
            }
        })
    
    @app.route("/api/test-email", methods=['POST'])
    def test_email():
        """Test email configuration"""
        try:
            success = email_service.test_connection()
            
            if success:
                # Send test email
                email_service.send_notification_async(
                    "Email Test",
                    "This is a test email to verify the email configuration is working correctly."
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Test email sent successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Email connection test failed'
                }), 500
                
        except Exception as e:
            logger.error(f"Email test error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route("/api/email-config")
    def email_config():
        """Get email configuration status"""
        status = email_service.get_status()
        
        return jsonify({
            'success': True,
            'config': {
                'enabled': status['enabled'],
                'configured': status['configured'],
                'recipients': status['recipients'],
                'queue_size': status['queue_size'],
                'worker_running': status['worker_running']
            }
        })
    
    logger.info("Flask application created successfully")
    return app


# Create the Flask application
app = create_app()

# Legacy compatibility - keep some functions available for existing imports
def format_stock_value(value, is_price=False, is_percent=False, is_volume=False):
    """Legacy function for backwards compatibility"""
    from core.utils import format_currency, format_percentage, format_number
    
    if is_percent:
        return format_percentage(value)
    elif is_price:
        return format_currency(value)
    elif is_volume:
        return format_number(value, use_commas=True)
    else:
        return format_number(value)


if __name__ == '__main__':
    # Development server
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )