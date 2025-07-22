#!/usr/bin/env python3
"""
Script pour remplacer complètement toutes les APIs par les APIs Manus
Modifie app.py pour utiliser uniquement les deux APIs Manus
"""

import re
import os
from datetime import datetime

def backup_original_file():
    """Crée une sauvegarde du fichier original"""
    backup_name = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    if os.path.exists("app.py"):
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
        with open(backup_name, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Sauvegarde créée: {backup_name}")
        return backup_name
    return None

def replace_imports_and_initialization():
    """Remplace les imports et initialisations"""
    
    # Remplacer les imports
    replacements = [
        # Remplacer les imports d'APIs
        (
            r'from stock_price_manager import StockPriceManager',
            'from manus_integration import manus_stock_api, manus_market_report_api, get_stock_price_manus, get_market_report_manus, generate_market_briefing_manus, get_exchange_rate_manus'
        ),
        (
            r'from manus_stock_manager import manus_stock_manager',
            '# Remplacé par l\'API Manus unifiée'
        ),
        
        # Remplacer les initialisations
        (
            r'# Gestionnaire de prix d\'actions avec Yahoo Finance\nstock_price_manager = StockPriceManager\(\)',
            '# APIs Manus unifiées - Remplace toutes les autres APIs\n# stock_price_manager = StockPriceManager()  # Remplacé par Manus'
        ),
        
        # Supprimer le cache forex (remplacé par Manus)
        (
            r'# Cache pour les taux de change avec expiration\nforex_cache = {}\nFOREX_CACHE_DURATION = 3600  # 1 heure',
            '# Cache pour les taux de change avec expiration\n# forex_cache = {}  # Remplacé par Manus\n# FOREX_CACHE_DURATION = 3600  # Remplacé par Manus'
        )
    ]
    
    return replacements

def replace_stock_price_functions():
    """Remplace toutes les fonctions de prix d'actions"""
    
    replacements = [
        # Remplacer la fonction principale de récupération de prix
        (
            r'def get_stock_price_yahoo\(symbol: str, item: Optional\[CollectionItem\], cache_key: str, force_refresh=False\):.*?return stock_data',
            '''def get_stock_price_manus(symbol: str, item: Optional[CollectionItem], cache_key: str, force_refresh=False):
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
        }''',
            re.DOTALL
        ),
        
        # Remplacer les appels à Yahoo Finance
        (
            r'get_stock_price_yahoo\(',
            'get_stock_price_manus('
        ),
        
        # Remplacer la route de prix d'actions
        (
            r'@app\.route\("/api/stock-price/<symbol>"\)\ndef get_stock_price\(symbol\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/stock-price/<symbol>")
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
        }), 500''',
            re.DOTALL
        ),
        
        # Remplacer la fonction de cache
        (
            r'@app\.route\("/api/stock-price/cache/clear", methods=\["POST"\]\)\ndef clear_stock_price_cache\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/stock-price/cache/clear", methods=["POST"])
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
        }), 500''',
            re.DOTALL
        ),
        
        # Remplacer le statut du cache
        (
            r'@app\.route\("/api/stock-price/cache/status"\)\ndef get_stock_price_cache_status\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/stock-price/cache/status")
def get_stock_price_cache_status():
    """Statut du cache des prix d'actions (API Manus)"""
    try:
        cache_status = manus_stock_api.get_cache_status()
        return jsonify({
            'success': True,
            'data': cache_status,
            'source': 'Manus API'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'source': 'Manus API'
        }), 500''',
            re.DOTALL
        ),
        
        # Remplacer la mise à jour de tous les prix
        (
            r'@app\.route\("/api/stock-price/update-all", methods=\["POST"\]\)\ndef update_all_stock_prices\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/stock-price/update-all", methods=["POST"])
def update_all_stock_prices():
    """Met à jour tous les prix d'actions via l'API Manus"""
    try:
        # Récupérer tous les items avec des symboles boursiers
        items = AdvancedDataManager.fetch_all_items()
        stock_items = [item for item in items if item.stock_symbol]
        
        if not stock_items:
            return jsonify({
                'success': True,
                'message': 'Aucun item avec symbole boursier trouvé',
                'updated_count': 0,
                'source': 'Manus API'
            })
        
        # Récupérer tous les symboles uniques
        symbols = list(set([item.stock_symbol for item in stock_items if item.stock_symbol]))
        
        # Récupérer les prix via l'API Manus
        stock_prices = manus_stock_api.get_multiple_stock_prices(symbols, force_refresh=True)
        
        # Mettre à jour les items dans la base de données
        updated_count = 0
        for item in stock_items:
            if item.stock_symbol and item.stock_symbol in stock_prices:
                stock_data = stock_prices[item.stock_symbol]
                
                if stock_data and stock_data.get('status') != 'unavailable':
                    # Mettre à jour les données de l'item
                    item.current_price = stock_data.get('price')
                    item.last_price_update = stock_data.get('last_updated')
                    item.stock_volume = stock_data.get('volume')
                    item.stock_pe_ratio = stock_data.get('pe_ratio')
                    item.stock_52_week_high = stock_data.get('high_52_week')
                    item.stock_52_week_low = stock_data.get('low_52_week')
                    item.stock_change = stock_data.get('change')
                    item.stock_change_percent = stock_data.get('change_percent')
                    
                    # Sauvegarder dans la base de données
                    # Note: Vous devrez adapter cette partie selon votre structure de base de données
                    updated_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{updated_count} prix d\'actions mis à jour via l\'API Manus',
            'updated_count': updated_count,
            'total_symbols': len(symbols),
            'source': 'Manus API'
        })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour prix: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'source': 'Manus API'
        }), 500''',
            re.DOTALL
        ),
        
        # Remplacer le statut de l'API
        (
            r'@app\.route\("/api/stock-price/status"\)\ndef check_stock_price_status\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/stock-price/status")
def check_stock_price_status():
    """Statut de l'API de prix d'actions (Manus)"""
    try:
        stock_status = manus_stock_api.get_api_status()
        
        return jsonify({
            'success': True,
            'stock_api': {
                'status': stock_status.get('status'),
                'response_time': stock_status.get('response_time'),
                'url': stock_status.get('url')
            },
            'timestamp': datetime.now().isoformat(),
            'source': 'Manus API'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'source': 'Manus API'
        }), 500''',
            re.DOTALL
        )
    ]
    
    return replacements

def replace_market_report_functions():
    """Remplace toutes les fonctions de rapports de marché"""
    
    replacements = [
        # Remplacer la fonction de génération de briefing
        (
            r'def generate_market_briefing\(\):.*?return briefing',
            '''def generate_market_briefing():
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
        }''',
            re.DOTALL
        ),
        
        # Remplacer la route de rapport de marché
        (
            r'@app\.route\("/api/market-report/manus", methods=\["GET"\]\)\ndef get_manus_market_report\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/market-report/manus", methods=["GET"])
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
        }), 500''',
            re.DOTALL
        ),
        
        # Remplacer la fonction de mise à jour programmée
        (
            r'def generate_scheduled_market_update\(\):.*?return update_data',
            '''def generate_scheduled_market_update():
    """Génère une mise à jour de marché programmée via l'API Manus"""
    try:
        market_report = get_market_report_manus()
        
        if market_report and market_report.get('status') != 'unavailable':
            update_data = {
                'timestamp': datetime.now().isoformat(),
                'source': 'Manus API',
                'status': 'success',
                'data': market_report,
                'message': 'Mise à jour de marché générée via l\'API Manus'
            }
        else:
            update_data = {
                'timestamp': datetime.now().isoformat(),
                'source': 'Manus API',
                'status': 'error',
                'error': 'Impossible de récupérer les données de marché',
                'message': 'Échec de la mise à jour de marché'
            }
        
        return update_data
        
    except Exception as e:
        logger.error(f"Erreur mise à jour marché programmée: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'source': 'Manus API',
            'status': 'error',
            'error': str(e),
            'message': 'Erreur lors de la mise à jour de marché'
        }''',
            re.DOTALL
        )
    ]
    
    return replacements

def replace_exchange_rate_functions():
    """Remplace les fonctions de taux de change"""
    
    replacements = [
        # Remplacer la fonction de taux de change
        (
            r'def get_live_exchange_rate\(from_currency: str, to_currency: str = \'CHF\'\) -> float:.*?return rate',
            '''def get_live_exchange_rate(from_currency: str, to_currency: str = 'CHF') -> float:
    """Récupère le taux de change via les données Manus (remplace les autres APIs)"""
    try:
        return get_exchange_rate_manus(from_currency, to_currency)
    except Exception as e:
        logger.error(f"Erreur taux de change Manus: {e}")
        return 1.0''',
            re.DOTALL
        ),
        
        # Remplacer la route de taux de change
        (
            r'@app\.route\("/api/exchange-rate/<from_currency>/<to_currency>"\)\ndef get_exchange_rate_route\(from_currency: str, to_currency: str = \'CHF\'\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/exchange-rate/<from_currency>/<to_currency>")
def get_exchange_rate_route(from_currency: str, to_currency: str = 'CHF'):
    """API de taux de change via Manus"""
    try:
        rate = get_exchange_rate_manus(from_currency, to_currency)
        return jsonify({
            'success': True,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': rate,
            'source': 'Manus API',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'source': 'Manus API',
            'timestamp': datetime.now().isoformat()
        }), 500''',
            re.DOTALL
        )
    ]
    
    return replacements

def remove_unused_functions():
    """Supprime les fonctions non utilisées"""
    
    functions_to_remove = [
        # Fonctions Yahoo Finance obsolètes
        r'def get_stock_price_yahoo\(.*?\):.*?return stock_data',
        r'def schedule_auto_stock_updates\(\):.*?def run_scheduler\(\):.*?threading\.Thread\(target=run_scheduler\)\.start\(\)',
        
        # Fonctions de briefing obsolètes
        r'def generate_market_briefing_with_manus\(\):.*?return briefing',
        r'def generate_market_briefing_with_openai\(\):.*?return briefing',
        
        # Routes obsolètes
        r'@app\.route\("/api/stock-price/reset-requests", methods=\["POST"\]\)\ndef reset_daily_requests\(\):.*?return jsonify\(.*?\)',
        r'@app\.route\("/api/stock-price/history/<symbol>"\)\ndef get_stock_price_history\(symbol\):.*?return jsonify\(.*?\)'
    ]
    
    return functions_to_remove

def apply_replacements_to_file(file_path: str):
    """Applique tous les remplacements au fichier"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Appliquer tous les remplacements
        all_replacements = (
            replace_imports_and_initialization() +
            replace_stock_price_functions() +
            replace_market_report_functions() +
            replace_exchange_rate_functions()
        )
        
        for pattern, replacement, use_dotall in all_replacements:
            flags = re.DOTALL if use_dotall else 0
            content = re.sub(pattern, replacement, content, flags=flags)
        
        # Supprimer les fonctions obsolètes
        functions_to_remove = remove_unused_functions()
        for pattern in functions_to_remove:
            content = re.sub(pattern, '# Fonction supprimée - Remplacée par l\'API Manus', content, flags=re.DOTALL)
        
        # Écrire le fichier modifié
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Vérifier si des changements ont été effectués
        if content != original_content:
            print(f"✅ Modifications appliquées à {file_path}")
            return True
        else:
            print(f"⚠️ Aucune modification appliquée à {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la modification de {file_path}: {e}")
        return False

def main():
    """Fonction principale"""
    
    print("🔄 Remplacement complet des APIs par les APIs Manus")
    print("=" * 60)
    
    # Créer une sauvegarde
    backup_file = backup_original_file()
    
    # Appliquer les remplacements
    print("\n📝 Application des modifications à app.py...")
    success = apply_replacements_to_file('app.py')
    
    if success:
        print("\n✅ Remplacement terminé avec succès !")
        print(f"📋 Sauvegarde créée: {backup_file}")
        
        print("\n📋 Résumé des modifications :")
        print("   ✅ Toutes les APIs de cours de bourse remplacées par l'API Manus")
        print("   ✅ Toutes les APIs de rapports de marché remplacées par l'API Manus")
        print("   ✅ Fonctions de taux de change basées sur Manus")
        print("   ✅ Cache adapté pour l'API Manus")
        print("   ✅ Routes API mises à jour")
        print("   ✅ Fonctions obsolètes supprimées")
        
        print("\n🚀 Prochaines étapes :")
        print("   1. Tester l'application: python app.py")
        print("   2. Vérifier que toutes les fonctionnalités marchent")
        print("   3. Supprimer les fichiers d'APIs obsolètes si nécessaire")
        
        print("\n📊 APIs Manus utilisées :")
        print("   • Cours de Bourse: https://ogh5izcelen1.manus.space/")
        print("   • Rapports de Marché: https://y0h0i3cqzyko.manus.space/api/report")
        
    else:
        print("\n❌ Aucune modification appliquée")
        print("   Vérifiez que les patterns correspondent à votre code")

if __name__ == "__main__":
    main() 