# Instructions d'Intégration des APIs Manus

## 🎯 Objectif
Remplacer toutes les autres APIs par les deux APIs Manus uniquement :
1. **API Cours de Bourse** : https://ogh5izcelen1.manus.space/
2. **API Rapports de Marché** : https://y0h0i3cqzyko.manus.space/api/report

## 📝 Étapes d'Intégration

### 1. Importer le module Manus
Ajoutez au début de votre `app.py` :
```python
from manus_integration import (
    manus_stock_api, 
    manus_market_report_api,
    get_stock_price_manus,
    get_market_report_manus,
    generate_market_briefing_manus,
    get_exchange_rate_manus
)
```

### 2. Remplacer les fonctions de prix d'actions
Remplacez toutes les fonctions de récupération de prix par :
```python
def get_stock_price_yahoo(symbol: str, item: Optional[CollectionItem], cache_key: str, force_refresh=False):
    """Remplacé par l'API Manus"""
    return get_stock_price_manus(symbol, force_refresh)
```

### 3. Remplacer les fonctions de rapports de marché
Remplacez toutes les fonctions de rapports par :
```python
def generate_market_briefing():
    """Remplacé par l'API Manus"""
    return generate_market_briefing_manus()
```

### 4. Remplacer les taux de change
Remplacez la fonction de taux de change par :
```python
def get_live_exchange_rate(from_currency: str, to_currency: str = 'CHF') -> float:
    """Remplacé par l'API Manus"""
    return get_exchange_rate_manus(from_currency, to_currency)
```

### 5. Mettre à jour les routes API
Remplacez les routes existantes par :
```python
@app.route("/api/stock-price/<symbol>")
def get_stock_price(symbol):
    """API Manus pour les prix d'actions"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        stock_data = get_stock_price_manus(symbol, force_refresh)
        return jsonify({'success': True, 'data': stock_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/market-report/manus", methods=["GET"])
def get_manus_market_report():
    """API Manus pour les rapports de marché"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        market_report = get_market_report_manus(force_refresh)
        return jsonify({'success': True, 'data': market_report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 6. Mettre à jour les fonctions de cache
```python
@app.route("/api/stock-price/cache/clear", methods=["POST"])
def clear_stock_price_cache():
    """Vide le cache des prix d'actions (Manus)"""
    try:
        result = manus_stock_api.clear_cache()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/stock-price/cache/status")
def get_stock_price_cache_status():
    """Statut du cache des prix d'actions (Manus)"""
    try:
        cache_status = manus_stock_api.get_cache_status()
        return jsonify({'success': True, 'data': cache_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

## 🔧 Fonctions Disponibles

### API Cours de Bourse
- `get_stock_price_manus(symbol, force_refresh=False)` : Prix d'une action
- `manus_stock_api.get_multiple_stock_prices(symbols, force_refresh=False)` : Prix multiples
- `manus_stock_api.clear_cache()` : Vider le cache
- `manus_stock_api.get_cache_status()` : Statut du cache

### API Rapports de Marché
- `get_market_report_manus(force_refresh=False)` : Rapport complet
- `generate_market_briefing_manus()` : Briefing de marché
- `manus_market_report_api.clear_cache()` : Vider le cache

### Taux de Change
- `get_exchange_rate_manus(from_currency, to_currency='CHF')` : Taux de change

## ✅ Avantages
- **Simplification** : Seulement 2 APIs au lieu de multiples
- **Cohérence** : Données uniformes
- **Performance** : Cache intégré
- **Fiabilité** : APIs testées et fonctionnelles

## 🚀 Test
Après intégration, testez avec :
```python
# Test prix d'action
stock_data = get_stock_price_manus('AAPL')
print(stock_data)

# Test rapport de marché
market_report = get_market_report_manus()
print(market_report)

# Test briefing
briefing = generate_market_briefing_manus()
print(briefing)
```
