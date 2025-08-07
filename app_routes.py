from flask import Blueprint, jsonify, render_template, request
from seeking_alpha_manager import logout as logout_seeking_alpha, get_movers as get_movers_seeking_alpha, get_stock_statistics as get_stock_statistics_seeking_alpha, get_news as get_news_seeking_alpha, get_market_summary as get_market_summary_seeking_alpha

seeking_alpha_blueprint = Blueprint('seeking_alpha', __name__)

@seeking_alpha_blueprint.route("/markets/seeking-alpha")
def seeking_alpha():
    """Render the Seeking Alpha page."""
    return render_template("seeking_alpha.html")

@seeking_alpha_blueprint.route("/api/markets/seeking-alpha/logout", methods=["POST"])
def seeking_alpha_logout():
    """Logout from Seeking Alpha API."""
    response = logout_seeking_alpha()
    if response:
        return jsonify(response)
    return jsonify({"status": "error", "message": "Failed to logout from Seeking Alpha"}), 500

@seeking_alpha_blueprint.route("/api/markets/seeking-alpha/movers", methods=["GET"])
def seeking_alpha_movers():
    """Get market movers from Seeking Alpha API."""
    region = request.args.get("region", "US")
    response = get_movers_seeking_alpha(region)
    if response:
        return jsonify(response)
    return jsonify({"status": "error", "message": "Failed to get market movers from Seeking Alpha"}), 500

@seeking_alpha_blueprint.route("/api/markets/seeking-alpha/stock-statistics", methods=["GET"])
def seeking_alpha_stock_statistics():
    """Get stock statistics from Seeking Alpha API."""
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"status": "error", "message": "Symbol is required"}), 400
    response = get_stock_statistics_seeking_alpha(symbol)
    if response:
        return jsonify(response)
    return jsonify({"status": "error", "message": "Failed to get stock statistics from Seeking Alpha"}), 500

@seeking_alpha_blueprint.route("/api/markets/seeking-alpha/news", methods=["GET"])
def seeking_alpha_news():
    """Get news from Seeking Alpha API."""
    response = get_news_seeking_alpha()
    if response:
        return jsonify(response)
    return jsonify({"status": "error", "message": "Failed to get news from Seeking Alpha"}), 500

@seeking_alpha_blueprint.route("/api/markets/seeking-alpha/market-summary", methods=["GET"])
def seeking_alpha_market_summary():
    """Get market summary from Seeking Alpha API."""
    region = request.args.get("region", "US")
    response = get_market_summary_seeking_alpha(region)
    if response:
        return jsonify(response)
    return jsonify({"status": "error", "message": "Failed to get market summary from Seeking Alpha"}), 500

