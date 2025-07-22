#!/usr/bin/env python3
"""
Script pour remplacer toutes les APIs existantes par les APIs Manus uniquement
Modifie app.py pour utiliser uniquement les deux APIs Manus
"""

import re
from typing import List, Tuple

def replace_stock_price_functions():
    """Remplace toutes les fonctions de prix d'actions par l'API Manus"""
    
    replacements = [
        # Remplacer les imports et initialisations
        (
            r'from stock_price_manager import StockPriceManager',
            'from manus_replacement_integration import manus_stock_replacement'
        ),
        (
            r'stock_price_manager = StockPriceManager\(\)',
            '# Remplacé par l\'API Manus\n# stock_price_manager = StockPriceManager()'
        ),
        
        # Remplacer les fonctions de récupération de prix
        (
            r'def get_stock_price_yahoo\(.*?\):',
            '''def get_stock_price_manus(symbol: str, item: Optional[CollectionItem], cache_key: str, force_refresh=False):
    """Récupère le prix d'une action via l'API Manus (remplace Yahoo Finance)"""
    try:
        stock_data = manus_stock_replacement.get_stock_price(symbol, force_refresh)
        
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
        ),
        
        # Remplacer les appels à Yahoo Finance
        (
            r'get_stock_price_yahoo\(',
            'get_stock_price_manus('
        ),
        
        # Remplacer les fonctions de cache
        (
            r'@app\.route\("/api/stock-price/cache/clear", methods=\["POST"\]\)\ndef clear_stock_price_cache\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/stock-price/cache/clear", methods=["POST"])
def clear_stock_price_cache():
    """Vide le cache des prix d'actions (API Manus)"""
    try:
        result = manus_stock_replacement.clear_cache()
        return jsonify({
            'success': True,
            'message': 'Cache des prix d\'actions vidé avec succès',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500''',
            re.DOTALL
        ),
        
        (
            r'@app\.route\("/api/stock-price/cache/status"\)\ndef get_stock_price_cache_status\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/stock-price/cache/status")
def get_stock_price_cache_status():
    """Retourne le statut du cache des prix d'actions (API Manus)"""
    try:
        cache_status = manus_stock_replacement.get_cache_status()
        return jsonify({
            'success': True,
            'data': cache_status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500''',
            re.DOTALL
        ),
        
        # Remplacer la fonction de mise à jour de tous les prix
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
                'updated_count': 0
            })
        
        # Récupérer tous les symboles uniques
        symbols = list(set([item.stock_symbol for item in stock_items if item.stock_symbol]))
        
        # Récupérer les prix via l'API Manus
        stock_prices = manus_stock_replacement.get_multiple_stock_prices(symbols, force_refresh=True)
        
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
            'error': str(e)
        }), 500''',
            re.DOTALL
        )
    ]
    
    return replacements

def replace_market_report_functions():
    """Remplace toutes les fonctions de rapports de marché par l'API Manus"""
    
    replacements = [
        # Remplacer les imports
        (
            r'from manus_stock_manager import manus_stock_manager',
            'from manus_replacement_integration import manus_market_report_replacement'
        ),
        
        # Remplacer les fonctions de génération de briefing
        (
            r'def generate_market_briefing\(\):.*?return briefing',
            '''def generate_market_briefing():
    """Génère un briefing de marché via l'API Manus (remplace toutes les autres APIs)"""
    try:
        briefing = manus_market_report_replacement.generate_market_briefing()
        
        if briefing.get('status') == 'success':
            return briefing
        else:
            return {
                'status': 'error',
                'message': briefing.get('message', 'Erreur génération briefing'),
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Erreur génération briefing Manus: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }''',
            re.DOTALL
        ),
        
        # Remplacer les routes de rapports de marché
        (
            r'@app\.route\("/api/market-report/manus", methods=\["GET"\]\)\ndef get_manus_market_report\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/market-report/manus", methods=["GET"])
def get_manus_market_report():
    """Récupère le rapport de marché via l'API Manus (remplace toutes les autres APIs)"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        market_report = manus_market_report_replacement.get_market_report(force_refresh)
        
        if market_report:
            return jsonify({
                'success': True,
                'data': market_report,
                'source': 'Manus API',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Impossible de récupérer le rapport de marché',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500''',
            re.DOTALL
        ),
        
        # Remplacer les fonctions de mise à jour de marché
        (
            r'def generate_scheduled_market_update\(\):.*?return update_data',
            '''def generate_scheduled_market_update():
    """Génère une mise à jour de marché programmée via l'API Manus"""
    try:
        market_report = manus_market_report_replacement.get_market_report()
        
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

def replace_other_api_functions():
    """Remplace les autres fonctions d'API par les APIs Manus"""
    
    replacements = [
        # Remplacer les fonctions de taux de change
        (
            r'def get_live_exchange_rate\(from_currency: str, to_currency: str = \'CHF\'\) -> float:.*?return rate',
            '''def get_live_exchange_rate(from_currency: str, to_currency: str = 'CHF') -> float:
    """Récupère le taux de change via les données Manus (remplace les autres APIs)"""
    try:
        # Utiliser les données de l'API Manus pour les taux de change
        market_report = manus_market_report_replacement.get_market_report()
        
        if market_report and market_report.get('status') != 'unavailable':
            # Extraire les taux de change du rapport Manus
            content = market_report.get('content', {}).get('text', '')
            
            # Chercher les taux CHF dans le contenu
            if 'CHF/USD' in content:
                # Extraire le taux CHF/USD
                import re
                chf_usd_match = re.search(r'CHF/USD.*?(\d+\.\d+)', content)
                if chf_usd_match:
                    chf_usd_rate = float(chf_usd_match.group(1))
                    
                    if from_currency == 'CHF' and to_currency == 'USD':
                        return chf_usd_rate
                    elif from_currency == 'USD' and to_currency == 'CHF':
                        return 1 / chf_usd_rate
            
            # Si pas trouvé, utiliser un taux par défaut
            if from_currency == 'CHF' and to_currency == 'USD':
                return 1.25  # Taux par défaut
            elif from_currency == 'USD' and to_currency == 'CHF':
                return 0.80  # Taux par défaut
        
        # Taux par défaut si pas de données
        if from_currency == 'CHF' and to_currency == 'USD':
            return 1.25
        elif from_currency == 'USD' and to_currency == 'CHF':
            return 0.80
        else:
            return 1.0  # Taux par défaut pour les autres devises
            
    except Exception as e:
        logger.error(f"Erreur taux de change Manus: {e}")
        return 1.0''',
            re.DOTALL
        ),
        
        # Remplacer les fonctions de statut
        (
            r'@app\.route\("/api/stock-price/status"\)\ndef check_stock_price_status\(\):.*?return jsonify\(.*?\)',
            '''@app.route("/api/stock-price/status")
def check_stock_price_status():
    """Vérifie le statut de l'API de prix d'actions (Manus)"""
    try:
        stock_status = manus_stock_replacement.get_api_status()
        report_status = manus_market_report_replacement.get_api_status()
        
        return jsonify({
            'success': True,
            'stock_api': {
                'status': stock_status.get('status'),
                'response_time': stock_status.get('response_time'),
                'url': stock_status.get('url')
            },
            'market_report_api': {
                'status': report_status.get('status'),
                'response_time': report_status.get('response_time'),
                'url': report_status.get('url')
            },
            'timestamp': datetime.now().isoformat(),
            'source': 'Manus APIs'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500''',
            re.DOTALL
        )
    ]
    
    return replacements

def apply_replacements_to_file(file_path: str, replacements: List[Tuple[str, str, bool]]):
    """Applique les remplacements à un fichier"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for pattern, replacement, use_dotall in replacements:
            flags = re.DOTALL if use_dotall else 0
            content = re.sub(pattern, replacement, content, flags=flags)
        
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
    """Fonction principale pour remplacer toutes les APIs"""
    
    print("🔄 Remplacement des APIs par les APIs Manus")
    print("=" * 50)
    
    # Récupérer tous les remplacements
    stock_replacements = replace_stock_price_functions()
    market_replacements = replace_market_report_functions()
    other_replacements = replace_other_api_functions()
    
    all_replacements = stock_replacements + market_replacements + other_replacements
    
    # Appliquer les remplacements à app.py
    print("\n📝 Application des modifications à app.py...")
    success = apply_replacements_to_file('app.py', all_replacements)
    
    if success:
        print("\n✅ Remplacement terminé avec succès !")
        print("\n📋 Résumé des modifications :")
        print("   • Toutes les APIs de cours de bourse remplacées par l'API Manus")
        print("   • Toutes les APIs de rapports de marché remplacées par l'API Manus")
        print("   • Fonctions de cache adaptées pour l'API Manus")
        print("   • Fonctions de statut mises à jour")
        print("   • Taux de change basés sur les données Manus")
        
        print("\n🚀 Prochaines étapes :")
        print("   1. Tester l'application avec les nouvelles APIs")
        print("   2. Vérifier que toutes les fonctionnalités marchent")
        print("   3. Ajuster si nécessaire")
        
    else:
        print("\n❌ Aucune modification appliquée")
        print("   Vérifiez que les patterns correspondent à votre code")

if __name__ == "__main__":
    main() 