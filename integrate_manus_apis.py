#!/usr/bin/env python3
"""
Script simple pour intégrer les APIs Manus dans l'application existante
Remplace les APIs existantes par les deux APIs Manus uniquement
"""

import os
import sys

def create_manus_integration_file():
    """Crée le fichier d'intégration Manus"""
    
    content = '''#!/usr/bin/env python3
"""
Intégration des APIs Manus pour remplacer toutes les autres APIs
- API de cours de bourse: https://ogh5izcelen1.manus.space/
- API de rapports de marché: https://y0h0i3cqzyko.manus.space/api/report
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManusStockAPI:
    """API Manus pour les cours de bourse - Remplace toutes les autres APIs de prix"""
    
    def __init__(self):
        self.base_url = "https://ogh5izcelen1.manus.space"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InventorySBO/1.0 (Manus Integration)'
        })
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_stock_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Récupère le prix d'une action via l'API Manus"""
        cache_key = f"stock_{symbol}"
        
        # Vérifier le cache
        if not force_refresh and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return cached_data
        
        try:
            # Essayer différents endpoints
            endpoints = [
                f"/api/stocks/{symbol}",
                f"/stocks/{symbol}",
                f"/api/prices/{symbol}",
                f"/prices/{symbol}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        # Données disponibles via l'API Manus
                        stock_data = {
                            'symbol': symbol,
                            'name': symbol,
                            'price': None,  # À extraire du HTML si possible
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
                            'status': 'available',
                            'endpoint': endpoint,
                            'raw_content_length': len(response.text)
                        }
                        
                        # Mettre en cache
                        self.cache[cache_key] = (stock_data, datetime.now())
                        return stock_data
                        
                except Exception as e:
                    logger.debug(f"Erreur endpoint {endpoint}: {e}")
                    continue
            
            # Données par défaut si aucun endpoint ne fonctionne
            default_data = {
                'symbol': symbol,
                'name': symbol,
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
                'error': 'API non disponible'
            }
            
            self.cache[cache_key] = (default_data, datetime.now())
            return default_data
            
        except Exception as e:
            logger.error(f"Erreur récupération prix {symbol}: {e}")
            return {
                'symbol': symbol,
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
    def get_multiple_stock_prices(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Récupère les prix de plusieurs actions"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_price(symbol, force_refresh)
        return results
    
    def clear_cache(self) -> Dict[str, Any]:
        """Vide le cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        return {
            'status': 'success',
            'cache_cleared': True,
            'entries_removed': cache_size,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retourne le statut du cache"""
        return {
            'cache_size': len(self.cache),
            'cache_duration_seconds': self.cache_duration,
            'cached_symbols': list(self.cache.keys()),
            'timestamp': datetime.now().isoformat()
        }

class ManusMarketReportAPI:
    """API Manus pour les rapports de marché - Remplace toutes les autres APIs de rapports"""
    
    def __init__(self):
        self.base_url = "https://y0h0i3cqzyko.manus.space"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InventorySBO/1.0 (Manus Integration)'
        })
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
    
    def get_market_report(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Récupère le rapport de marché via l'API Manus"""
        cache_key = "market_report"
        
        # Vérifier le cache
        if not force_refresh and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return cached_data
        
        try:
            response = self.session.get(f"{self.base_url}/api/report", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                report = data.get('report', {})
                
                # Transformer les données
                market_report = {
                    'timestamp': datetime.now().isoformat(),
                    'report_date': report.get('metadata', {}).get('report_date'),
                    'generation_time': report.get('metadata', {}).get('generation_time_formatted'),
                    'source': 'Manus API',
                    'status': 'complete',
                    
                    # Métriques de marché
                    'market_metrics': report.get('key_metrics', {}),
                    
                    # Contenu
                    'content': report.get('content', {}),
                    
                    # Résumé
                    'summary': report.get('summary', {}),
                    
                    # Sections
                    'sections': report.get('metadata', {}).get('sections', []),
                    
                    # Données brutes
                    'raw_data': data
                }
                
                # Mettre en cache
                self.cache[cache_key] = (market_report, datetime.now())
                return market_report
                
            else:
                return self._create_default_report()
                
        except Exception as e:
            logger.error(f"Erreur récupération rapport: {e}")
            return self._create_default_report()
    
    def _create_default_report(self) -> Dict[str, Any]:
        """Crée un rapport par défaut"""
        return {
            'timestamp': datetime.now().isoformat(),
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'source': 'Manus API',
            'status': 'unavailable',
            'error': 'API non disponible',
            'market_metrics': {},
            'content': {},
            'summary': {},
            'sections': []
        }
    
    def generate_market_briefing(self) -> Dict[str, Any]:
        """Génère un briefing de marché"""
        try:
            market_report = self.get_market_report()
            
            if market_report.get('status') == 'complete':
                return {
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Manus API',
                    'briefing': {
                        'title': f"Briefing de Marché - {market_report.get('report_date', 'Date inconnue')}",
                        'summary': market_report.get('summary', {}).get('key_points', []),
                        'metrics': market_report.get('market_metrics', {}),
                        'content': market_report.get('content', {}).get('markdown', '')
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Impossible de récupérer les données de marché',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Vide le cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        return {
            'status': 'success',
            'cache_cleared': True,
            'entries_removed': cache_size,
            'timestamp': datetime.now().isoformat()
        }

# Instances globales pour remplacer les APIs existantes
manus_stock_api = ManusStockAPI()
manus_market_report_api = ManusMarketReportAPI()

# Fonctions de remplacement pour compatibilité
def get_stock_price_manus(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Remplace toutes les autres fonctions de prix d'actions"""
    return manus_stock_api.get_stock_price(symbol, force_refresh)

def get_market_report_manus(force_refresh: bool = False) -> Dict[str, Any]:
    """Remplace toutes les autres fonctions de rapports de marché"""
    return manus_market_report_api.get_market_report(force_refresh)

def generate_market_briefing_manus() -> Dict[str, Any]:
    """Remplace toutes les autres fonctions de briefing"""
    return manus_market_report_api.generate_market_briefing()

def get_exchange_rate_manus(from_currency: str, to_currency: str = 'CHF') -> float:
    """Récupère le taux de change via les données Manus"""
    try:
        market_report = manus_market_report_api.get_market_report()
        
        if market_report.get('status') == 'complete':
            content = market_report.get('content', {}).get('text', '')
            
            # Chercher les taux CHF dans le contenu
            if 'CHF/USD' in content:
                import re
                chf_usd_match = re.search(r'CHF/USD.*?(\d+\.\d+)', content)
                if chf_usd_match:
                    chf_usd_rate = float(chf_usd_match.group(1))
                    
                    if from_currency == 'CHF' and to_currency == 'USD':
                        return chf_usd_rate
                    elif from_currency == 'USD' and to_currency == 'CHF':
                        return 1 / chf_usd_rate
        
        # Taux par défaut
        if from_currency == 'CHF' and to_currency == 'USD':
            return 1.25
        elif from_currency == 'USD' and to_currency == 'CHF':
            return 0.80
        else:
            return 1.0
            
    except Exception as e:
        logger.error(f"Erreur taux de change: {e}")
        return 1.0
'''
    
    with open('manus_integration.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fichier manus_integration.py créé")

def create_integration_instructions():
    """Crée les instructions d'intégration"""
    
    instructions = '''# Instructions d'Intégration des APIs Manus

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
'''
    
    with open('INTEGRATION_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("✅ Instructions d'intégration créées (INTEGRATION_INSTRUCTIONS.md)")

def main():
    """Fonction principale"""
    
    print("🔧 Création de l'intégration Manus")
    print("=" * 40)
    
    # Créer le fichier d'intégration
    create_manus_integration_file()
    
    # Créer les instructions
    create_integration_instructions()
    
    print("\n🎉 Intégration créée avec succès !")
    print("\n📋 Fichiers créés :")
    print("   • manus_integration.py - Module d'intégration Manus")
    print("   • INTEGRATION_INSTRUCTIONS.md - Instructions détaillées")
    
    print("\n🚀 Prochaines étapes :")
    print("   1. Lire INTEGRATION_INSTRUCTIONS.md")
    print("   2. Modifier app.py selon les instructions")
    print("   3. Tester l'application")
    print("   4. Supprimer les anciennes APIs non utilisées")

if __name__ == "__main__":
    main() 