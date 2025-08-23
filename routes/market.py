"""
Routes for market data and stock price functionality.
"""

from flask import Blueprint, jsonify, request
import logging
from services.market_service import market_service
from services.email_service import email_service

logger = logging.getLogger(__name__)

market_bp = Blueprint('market', __name__, url_prefix='/api')


@market_bp.route('/stock-price/<symbol>', methods=['GET'])
def get_stock_price(symbol):
    """Get stock price for a symbol"""
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        price_data = market_service.get_stock_price(symbol, force_refresh=force_refresh)
        
        if price_data:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'data': price_data
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No price data available for {symbol}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting stock price for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/stock-price/update-all', methods=['POST'])
def update_all_stock_prices():
    """Update all stock prices in the database"""
    try:
        result = market_service.update_all_stock_prices()
        
        if result['success']:
            # Send email notification if significant updates
            if result['updated'] > 0:
                email_service.send_notification_async(
                    f"Stock Prices Updated: {result['updated']} items",
                    f"Successfully updated {result['updated']} stock prices out of {result['total']} items."
                )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error updating all stock prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/stock-price/cache/clear', methods=['POST'])
def clear_stock_price_cache():
    """Clear stock price cache"""
    try:
        market_service.clear_cache()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/stock-price/cache/status', methods=['GET'])
def get_cache_status():
    """Get cache status"""
    try:
        status = market_service.get_cache_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/exchange-rate/<from_currency>/<to_currency>', methods=['GET'])
def get_exchange_rate_route(from_currency: str, to_currency: str = 'CHF'):
    """Get exchange rate between currencies"""
    try:
        rate = market_service.get_exchange_rate(from_currency, to_currency)
        
        return jsonify({
            'success': True,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': rate,
            'formatted': f"1 {from_currency} = {rate:.4f} {to_currency}"
        })
        
    except Exception as e:
        logger.error(f"Error getting exchange rate {from_currency}->{to_currency}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/market-briefing', methods=['GET'])
def get_market_briefing():
    """Get market briefing"""
    try:
        briefing_type = request.args.get('type', 'daily')
        briefing = market_service.get_market_briefing(briefing_type)
        
        if briefing:
            return jsonify({
                'success': True,
                'briefing': briefing,
                'type': briefing_type
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No market briefing available'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting market briefing: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/daily-news', methods=['GET'])
def get_daily_news():
    """Get daily market news"""
    try:
        news = market_service.get_daily_news()
        
        return jsonify({
            'success': True,
            'news': news or [],
            'count': len(news) if news else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting daily news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/market-alerts', methods=['GET'])
def get_market_alerts():
    """Get market alerts"""
    try:
        alerts = market_service.get_market_alerts()
        
        return jsonify({
            'success': True,
            'alerts': alerts or [],
            'count': len(alerts) if alerts else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting market alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/stock-price/history/<symbol>', methods=['GET'])
def get_stock_price_history(symbol):
    """Get stock price history"""
    try:
        days = int(request.args.get('days', 30))
        history = market_service.get_stock_history(symbol, days)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'history': history or [],
            'days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting stock history for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@market_bp.route('/send-market-report-email', methods=['POST'])
def send_market_report_email():
    """Send market report via email"""
    try:
        # Get market data
        briefing = market_service.get_market_briefing()
        news = market_service.get_daily_news()
        
        # Prepare report data
        report_data = {
            'briefing': briefing,
            'news': news[:5] if news else [],  # Top 5 news items
            'timestamp': market_service.get_cache_status()
        }
        
        # Send email
        success = email_service.send_market_report(report_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Market report email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send market report email'
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending market report email: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500