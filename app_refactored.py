"""
Refactored Flask application for Inventory SBO.
This is a completely restructured version of the original app.py with modular architecture.
"""

import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS

# Core imports
from core.config import Config
from core.database import db_manager

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


def create_app():
    """Application factory pattern"""
    
    # Validate configuration first
    if not Config.validate():
        raise RuntimeError("Invalid configuration")
    
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
        return render_template('dashboard.html')
    
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
        return render_template('real-estate.html')
    
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
                'timestamp': '2024-01-01T00:00:00Z',  # Would be actual timestamp
                'services': {
                    'database': 'connected' if db_connected else 'disconnected',
                    'ai': 'available' if ai_available else 'unavailable',
                    'email': 'enabled' if email_status['enabled'] else 'disabled',
                    'market': 'active' if market_status['managers_status'] else 'inactive'
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
    
    logger.info("✅ Flask application created successfully")
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