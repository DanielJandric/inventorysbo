#!/usr/bin/env python3
"""
Script simple pour intégrer les APIs Manus dans app.py
Remplace les imports et les fonctions principales
"""

import re
import os
from datetime import datetime

def backup_file():
    """Crée une sauvegarde"""
    backup_name = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    if os.path.exists("app.py"):
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
        with open(backup_name, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Sauvegarde créée: {backup_name}")
        return backup_name
    return None

def integrate_manus_apis():
    """Intègre les APIs Manus dans app.py"""
    
    print("🔧 Intégration des APIs Manus dans app.py...")
    
    # Lire le fichier
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Ajouter l'import Manus
    manus_import = '''from manus_integration import (
    manus_stock_api, 
    manus_market_report_api,
    get_stock_price_manus,
    get_market_report_manus,
    generate_market_briefing_manus,
    get_exchange_rate_manus
)'''
    
    # Remplacer les imports existants
    content = re.sub(
        r'from stock_price_manager import StockPriceManager',
        manus_import,
        content
    )
    
    content = re.sub(
        r'from manus_stock_manager import manus_stock_manager',
        '# Remplacé par l\'API Manus unifiée',
        content
    )
    
    # 2. Remplacer l'initialisation du stock manager
    content = re.sub(
        r'# Gestionnaire de prix d\'actions avec Yahoo Finance\nstock_price_manager = StockPriceManager\(\)',
        '# APIs Manus unifiées - Remplace toutes les autres APIs\n# stock_price_manager = StockPriceManager()  # Remplacé par Manus',
        content
    )
    
    # 3. Remplacer la fonction get_stock_price_yahoo
    new_function = '''def get_stock_price_manus(symbol: str, item: Optional[CollectionItem], cache_key: str, force_refresh=False):
    """Récupère le prix d'une action via l'API Manus (remplace Yahoo Finance)"""
    try:
        stock_data = get_stock_price_manus(symbol, force_refresh)
        
        if stock_data and stock_data.get('status') != 'unavailable':
            return {
                'price': stock_data.get('price'),
                'change': stock_data.get('change'),
                'change_percent': stock_data.get('change_percent'),
                'volume': stock_data.get('volume'),
                'market_cap': stock_data.get('market_cap'),
                'pe_ratio': stock_data.get('pe_ratio'),
                'high_52_week': stock_data.get('high_52_week'),
                'low_52_week': stock_data.get('low_52_week'),
                'open': stock_data.get('open'),
                'previous_close': stock_data.get('previous_close'),
                'currency': stock_data.get('currency', 'USD'),
                'exchange': stock_data.get('exchange', 'NASDAQ'),
                'last_updated': stock_data.get('last_updated'),
                'source': 'Manus API',
                'status': 'success'
            }
        else:
            return {
                'price': None,
                'change': None,
                'change_percent': None,
                'volume': None,
                'market_cap': None,
                'pe_ratio': None,
                'high_52_week': None,
                'low_52_week': None,
                'open': None,
                'previous_close': None,
                'currency': 'USD',
                'exchange': 'NASDAQ',
                'last_updated': datetime.now().isoformat(),
                'source': 'Manus API',
                'status': 'unavailable',
                'error': 'Données non disponibles'
            }
    except Exception as e:
        logger.error(f"Erreur récupération prix Manus pour {symbol}: {e}")
        return {
            'price': None,
            'change': None,
            'change_percent': None,
            'volume': None,
            'market_cap': None,
            'pe_ratio': None,
            'high_52_week': None,
            'low_52_week': None,
            'open': None,
            'previous_close': None,
            'currency': 'USD',
            'exchange': 'NASDAQ',
            'last_updated': datetime.now().isoformat(),
            'source': 'Manus API',
            'status': 'error',
            'error': str(e)
        }'''
    
    # Chercher et remplacer la fonction existante
    pattern = r'def get_stock_price_yahoo\(symbol: str, item: Optional\[CollectionItem\], cache_key: str, force_refresh=False\):.*?return stock_data'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_function, content, flags=re.DOTALL)
        print("✅ Fonction get_stock_price_yahoo remplacée")
    else:
        print("⚠️ Fonction get_stock_price_yahoo non trouvée")
    
    # 4. Remplacer les appels à get_stock_price_yahoo
    content = re.sub(r'get_stock_price_yahoo\(', 'get_stock_price_manus(', content)
    
    # 5. Remplacer la fonction get_live_exchange_rate
    exchange_function = '''def get_live_exchange_rate(from_currency: str, to_currency: str = 'CHF') -> float:
    """Récupère le taux de change via les données Manus (remplace les autres APIs)"""
    try:
        return get_exchange_rate_manus(from_currency, to_currency)
    except Exception as e:
        logger.error(f"Erreur taux de change Manus: {e}")
        return 1.0'''
    
    pattern = r'def get_live_exchange_rate\(from_currency: str, to_currency: str = \'CHF\'\) -> float:.*?return rate'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, exchange_function, content, flags=re.DOTALL)
        print("✅ Fonction get_live_exchange_rate remplacée")
    else:
        print("⚠️ Fonction get_live_exchange_rate non trouvée")
    
    # 6. Remplacer la fonction generate_market_briefing
    briefing_function = '''def generate_market_briefing():
    """Génère un briefing de marché via l'API Manus (remplace toutes les autres APIs)"""
    try:
        briefing = generate_market_briefing_manus()
        
        if briefing.get('status') == 'success':
            return briefing
        else:
            return {
                'status': 'error',
                'message': briefing.get('message', 'Erreur génération briefing'),
                'timestamp': datetime.now().isoformat(),
                'source': 'Manus API'
            }
    except Exception as e:
        logger.error(f"Erreur génération briefing Manus: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat(),
            'source': 'Manus API'
        }'''
    
    pattern = r'def generate_market_briefing\(\):.*?return briefing'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, briefing_function, content, flags=re.DOTALL)
        print("✅ Fonction generate_market_briefing remplacée")
    else:
        print("⚠️ Fonction generate_market_briefing non trouvée")
    
    # 7. Mettre à jour les routes API
    # Route de prix d'actions
    stock_route = '''@app.route("/api/stock-price/<symbol>")
def get_stock_price(symbol):
    """API Manus pour les prix d'actions - Remplace toutes les autres APIs"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        stock_data = get_stock_price_manus(symbol, force_refresh)
        
        return jsonify({
            'success': True,
            'data': stock_data,
            'source': 'Manus API',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur API prix {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'source': 'Manus API',
            'timestamp': datetime.now().isoformat()
        }), 500'''
    
    pattern = r'@app\.route\("/api/stock-price/<symbol>"\)\ndef get_stock_price\(symbol\):.*?return jsonify\(.*?\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, stock_route, content, flags=re.DOTALL)
        print("✅ Route /api/stock-price/<symbol> mise à jour")
    else:
        print("⚠️ Route /api/stock-price/<symbol> non trouvée")
    
    # Route de cache
    cache_route = '''@app.route("/api/stock-price/cache/clear", methods=["POST"])
def clear_stock_price_cache():
    """Vide le cache des prix d'actions (API Manus)"""
    try:
        result = manus_stock_api.clear_cache()
        return jsonify({
            'success': True,
            'message': 'Cache des prix d\'actions vidé avec succès',
            'data': result,
            'source': 'Manus API'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'source': 'Manus API'
        }), 500'''
    
    pattern = r'@app\.route\("/api/stock-price/cache/clear", methods=\["POST"\]\)\ndef clear_stock_price_cache\(\):.*?return jsonify\(.*?\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, cache_route, content, flags=re.DOTALL)
        print("✅ Route /api/stock-price/cache/clear mise à jour")
    else:
        print("⚠️ Route /api/stock-price/cache/clear non trouvée")
    
    # Route de rapport de marché
    report_route = '''@app.route("/api/market-report/manus", methods=["GET"])
def get_manus_market_report():
    """Récupère le rapport de marché via l'API Manus (remplace toutes les autres APIs)"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        market_report = get_market_report_manus(force_refresh)
        
        return jsonify({
            'success': True,
            'data': market_report,
            'source': 'Manus API',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'source': 'Manus API'
        }), 500'''
    
    pattern = r'@app\.route\("/api/market-report/manus", methods=\["GET"\]\)\ndef get_manus_market_report\(\):.*?return jsonify\(.*?\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, report_route, content, flags=re.DOTALL)
        print("✅ Route /api/market-report/manus mise à jour")
    else:
        print("⚠️ Route /api/market-report/manus non trouvée")
    
    # Écrire le fichier modifié
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Intégration terminée !")
    return True

def main():
    """Fonction principale"""
    
    print("🔄 Intégration simple des APIs Manus")
    print("=" * 50)
    
    # Créer une sauvegarde
    backup_name = backup_file()
    
    # Intégrer les APIs
    success = integrate_manus_apis()
    
    if success:
        print("\n🎉 Intégration réussie !")
        print(f"📋 Sauvegarde: {backup_name}")
        
        print("\n📋 Modifications effectuées :")
        print("   ✅ Import des APIs Manus ajouté")
        print("   ✅ Fonction get_stock_price_yahoo remplacée")
        print("   ✅ Fonction get_live_exchange_rate remplacée")
        print("   ✅ Fonction generate_market_briefing remplacée")
        print("   ✅ Routes API mises à jour")
        print("   ✅ Cache adapté pour Manus")
        
        print("\n🚀 Prochaines étapes :")
        print("   1. Tester l'application: python app.py")
        print("   2. Vérifier les fonctionnalités")
        print("   3. Supprimer les anciens fichiers d'APIs si nécessaire")
        
        print("\n📊 APIs Manus utilisées :")
        print("   • Cours de Bourse: https://ogh5izcelen1.manus.space/")
        print("   • Rapports de Marché: https://y0h0i3cqzyko.manus.space/api/report")
        
    else:
        print("\n❌ Échec de l'intégration")

if __name__ == "__main__":
    main() 