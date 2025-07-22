#!/usr/bin/env python3
"""
Exemple d'intégration des APIs Manus dans l'application Flask existante
Ajoute des routes pour les rapports de marché et les cours de bourse
"""

from flask import Flask, jsonify, render_template, request
from manus_api_integration import ManusIntegrationManager, integrate_market_report_to_app, integrate_stock_prices_to_app
import json
from datetime import datetime

# Initialiser le gestionnaire d'intégration
manus_manager = ManusIntegrationManager()

def create_manus_routes(app):
    """Ajoute les routes Manus à l'application Flask"""
    
    @app.route('/api/manus/market-report')
    def get_manus_market_report():
        """Route pour récupérer le rapport des marchés Manus"""
        try:
            force_refresh = request.args.get('refresh', 'false').lower() == 'true'
            market_update = manus_manager.get_market_update(force_refresh)
            
            if market_update:
                return jsonify({
                    'success': True,
                    'data': market_update,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Impossible de récupérer le rapport des marchés',
                    'timestamp': datetime.now().isoformat()
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/manus/stock-prices')
    def get_manus_stock_prices():
        """Route pour récupérer les prix des actions Manus"""
        try:
            symbols = request.args.get('symbols', '')
            if not symbols:
                return jsonify({
                    'success': False,
                    'error': 'Paramètre symbols requis',
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            # Convertir la liste des symboles
            symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
            if not symbol_list:
                return jsonify({
                    'success': False,
                    'error': 'Aucun symbole valide fourni',
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            stock_prices = manus_manager.get_stock_prices(symbol_list)
            
            return jsonify({
                'success': True,
                'data': stock_prices,
                'symbols_requested': symbol_list,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/manus/complete-data')
    def get_manus_complete_data():
        """Route pour récupérer toutes les données Manus"""
        try:
            symbols = request.args.get('symbols', '')
            symbol_list = []
            
            if symbols:
                symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
            
            complete_data = manus_manager.get_complete_market_data(symbol_list)
            
            return jsonify({
                'success': True,
                'data': complete_data,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/manus/status')
    def get_manus_api_status():
        """Route pour vérifier le statut des APIs Manus"""
        try:
            # Vérifier le statut de l'API de rapport
            market_api_status = manus_manager.market_report_api.session.get(
                f"{manus_manager.market_report_api.base_url}/api/health",
                timeout=5
            ).status_code == 200
            
            # Vérifier le statut de l'API de cours
            stock_api_status = manus_manager.stock_api.get_api_status()
            
            return jsonify({
                'success': True,
                'data': {
                    'market_report_api': {
                        'status': 'online' if market_api_status else 'offline',
                        'url': manus_manager.market_report_api.base_url
                    },
                    'stock_api': stock_api_status or {
                        'status': 'offline',
                        'url': manus_manager.stock_api.base_url
                    },
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/manus/markets')
    def manus_markets_page():
        """Page pour afficher les rapports de marché Manus"""
        try:
            market_update = manus_manager.get_market_update()
            
            if market_update:
                return render_template('manus_markets.html', 
                                     market_data=market_update,
                                     timestamp=datetime.now().isoformat())
            else:
                return render_template('manus_markets.html', 
                                     market_data=None,
                                     error="Impossible de récupérer les données",
                                     timestamp=datetime.now().isoformat())
                
        except Exception as e:
            return render_template('manus_markets.html', 
                                 market_data=None,
                                 error=str(e),
                                 timestamp=datetime.now().isoformat())
    
    @app.route('/manus/stocks')
    def manus_stocks_page():
        """Page pour afficher les cours de bourse Manus"""
        try:
            # Récupérer les symboles depuis les paramètres ou utiliser des valeurs par défaut
            default_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
            symbols = request.args.get('symbols', ','.join(default_symbols))
            symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
            
            stock_prices = manus_manager.get_stock_prices(symbol_list)
            
            return render_template('manus_stocks.html', 
                                 stock_data=stock_prices,
                                 symbols=symbol_list,
                                 timestamp=datetime.now().isoformat())
                
        except Exception as e:
            return render_template('manus_stocks.html', 
                                 stock_data={},
                                 symbols=[],
                                 error=str(e),
                                 timestamp=datetime.now().isoformat())

# Exemple d'utilisation dans votre app.py existant
def integrate_manus_into_existing_app(app):
    """
    Fonction pour intégrer les routes Manus dans votre application existante
    
    Usage dans votre app.py:
    from manus_flask_integration import integrate_manus_into_existing_app
    
    app = Flask(__name__)
    integrate_manus_into_existing_app(app)
    """
    
    # Ajouter les routes Manus
    create_manus_routes(app)
    
    # Ajouter un menu dans la navigation (si vous en avez un)
    @app.context_processor
    def inject_manus_menu():
        """Injecte le menu Manus dans le contexte des templates"""
        return {
            'manus_menu': [
                {'url': '/manus/markets', 'title': 'Rapports Marchés Manus'},
                {'url': '/manus/stocks', 'title': 'Cours Bourse Manus'},
                {'url': '/api/manus/status', 'title': 'Statut APIs Manus'}
            ]
        }

# Exemple de template pour les rapports de marché
MANUS_MARKETS_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapports de Marché - Manus API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .content { margin: 20px 0; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #e8f4f8; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }
        .error { color: red; background: #ffe6e6; padding: 10px; border-radius: 5px; }
        .timestamp { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Rapports de Marché - Manus API</h1>
        <p class="timestamp">Dernière mise à jour: {{ timestamp }}</p>
    </div>
    
    {% if error %}
        <div class="error">
            <h3>❌ Erreur</h3>
            <p>{{ error }}</p>
        </div>
    {% elif market_data %}
        <div class="content">
            <h2>📈 Métriques Clés</h2>
            <div class="metrics">
                {% for key, value in market_data.key_metrics.items() %}
                    <div class="metric">
                        <strong>{{ key|title }}:</strong> {{ value }}%
                    </div>
                {% endfor %}
            </div>
            
            <h2>📋 Résumé</h2>
            <div class="section">
                {% if market_data.summary.key_points %}
                    <ul>
                    {% for point in market_data.summary.key_points %}
                        <li>{{ point }}</li>
                    {% endfor %}
                    </ul>
                {% endif %}
            </div>
            
            <h2>📝 Contenu Complet</h2>
            <div class="section">
                {% if market_data.content_markdown %}
                    <pre>{{ market_data.content_markdown }}</pre>
                {% endif %}
            </div>
            
            <h2>🔧 Informations Techniques</h2>
            <div class="section">
                <p><strong>Date du rapport:</strong> {{ market_data.report_date }}</p>
                <p><strong>Sections disponibles:</strong> {{ market_data.sections|length }}</p>
                <p><strong>Statut:</strong> {{ market_data.summary.status }}</p>
            </div>
        </div>
    {% else %}
        <div class="error">
            <h3>⚠️ Aucune donnée disponible</h3>
            <p>Impossible de récupérer les données de marché.</p>
        </div>
    {% endif %}
    
    <div class="header">
        <p><a href="/api/manus/market-report">API JSON</a> | 
           <a href="/manus/stocks">Cours de Bourse</a> | 
           <a href="/api/manus/status">Statut APIs</a></p>
    </div>
</body>
</html>
"""

# Exemple de template pour les cours de bourse
MANUS_STOCKS_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cours de Bourse - Manus API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .stock-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .stock-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .stock-card.available { background: #e8f5e8; }
        .stock-card.unavailable { background: #ffe6e6; }
        .error { color: red; background: #ffe6e6; padding: 10px; border-radius: 5px; }
        .timestamp { color: #666; font-size: 0.9em; }
        .form { margin: 20px 0; }
        .form input { padding: 10px; margin-right: 10px; }
        .form button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h1>💹 Cours de Bourse - Manus API</h1>
        <p class="timestamp">Dernière mise à jour: {{ timestamp }}</p>
    </div>
    
    <div class="form">
        <form method="GET">
            <input type="text" name="symbols" value="{{ symbols|join(',') }}" placeholder="AAPL,MSFT,GOOGL">
            <button type="submit">Actualiser</button>
        </form>
    </div>
    
    {% if error %}
        <div class="error">
            <h3>❌ Erreur</h3>
            <p>{{ error }}</p>
        </div>
    {% elif stock_data %}
        <div class="stock-grid">
            {% for symbol, data in stock_data.items() %}
                <div class="stock-card {% if data.available %}available{% else %}unavailable{% endif %}">
                    <h3>{{ symbol }}</h3>
                    {% if data.available %}
                        <p><strong>Format:</strong> {{ data.format }}</p>
                        {% if data.format == 'html' %}
                            <p><strong>URL:</strong> <a href="{{ data.url }}" target="_blank">Voir données</a></p>
                            <p><strong>Taille:</strong> {{ data.content_length }} caractères</p>
                        {% elif data.format == 'json' %}
                            <p><strong>Données JSON disponibles</strong></p>
                        {% endif %}
                    {% else %}
                        <p><strong>Statut:</strong> Non disponible</p>
                        {% if data.error %}
                            <p><strong>Erreur:</strong> {{ data.error }}</p>
                        {% endif %}
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        
        <div class="header">
            <h3>📊 Résumé</h3>
            <p>Actions disponibles: {{ stock_data.values()|selectattr('available')|list|length }}/{{ stock_data|length }}</p>
        </div>
    {% else %}
        <div class="error">
            <h3>⚠️ Aucune donnée disponible</h3>
            <p>Aucune donnée de cours de bourse n'est disponible.</p>
        </div>
    {% endif %}
    
    <div class="header">
        <p><a href="/api/manus/stock-prices?symbols={{ symbols|join(',') }}">API JSON</a> | 
           <a href="/manus/markets">Rapports Marchés</a> | 
           <a href="/api/manus/status">Statut APIs</a></p>
    </div>
</body>
</html>
"""

# Exemple d'utilisation
if __name__ == "__main__":
    print("🧪 Test d'intégration Flask Manus")
    print("=" * 50)
    
    # Créer une application Flask de test
    app = Flask(__name__)
    
    # Intégrer les routes Manus
    integrate_manus_into_existing_app(app)
    
    # Créer les templates
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    with open('templates/manus_markets.html', 'w', encoding='utf-8') as f:
        f.write(MANUS_MARKETS_TEMPLATE)
    
    with open('templates/manus_stocks.html', 'w', encoding='utf-8') as f:
        f.write(MANUS_STOCKS_TEMPLATE)
    
    print("✅ Templates créés")
    print("✅ Routes Manus intégrées")
    print("\n📋 Routes disponibles:")
    print("   • GET /api/manus/market-report - Rapport des marchés (JSON)")
    print("   • GET /api/manus/stock-prices?symbols=AAPL,MSFT - Prix actions (JSON)")
    print("   • GET /api/manus/complete-data - Données complètes (JSON)")
    print("   • GET /api/manus/status - Statut des APIs (JSON)")
    print("   • GET /manus/markets - Page rapports marchés (HTML)")
    print("   • GET /manus/stocks - Page cours bourse (HTML)")
    
    print("\n🎉 Intégration terminée !")
    print("💡 Pour utiliser dans votre app.py existant:")
    print("   from manus_flask_integration import integrate_manus_into_existing_app")
    print("   integrate_manus_into_existing_app(app)") 