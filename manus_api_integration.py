#!/usr/bin/env python3
"""
Module d'intégration pour les APIs Manus
- API de rapport des marchés: https://y0h0i3cqzyko.manus.space/api/report
- API de cours de bourse: https://ogh5izcelen1.manus.space/
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManusMarketReportAPI:
    """Classe pour interagir avec l'API de rapport des marchés Manus"""
    
    def __init__(self, base_url: str = "https://y0h0i3cqzyko.manus.space"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InventorySBO/1.0 (Manus Integration)'
        })
    
    def get_market_report(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Récupère le rapport des marchés
        
        Args:
            force_refresh: Si True, force le rafraîchissement des données
            
        Returns:
            Données du rapport ou None en cas d'erreur
        """
        try:
            params = {}
            if force_refresh:
                params['refresh'] = 'true'
            
            response = self.session.get(
                f"{self.base_url}/api/report",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Rapport des marchés récupéré - Fraîcheur: {data.get('data_freshness', 'N/A')}")
                return data
            else:
                logger.error(f"Erreur API rapport: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du rapport: {e}")
            return None
    
    def get_report_content(self, format_type: str = "markdown") -> Optional[str]:
        """
        Récupère le contenu du rapport dans le format spécifié
        
        Args:
            format_type: 'markdown' ou 'html'
            
        Returns:
            Contenu du rapport ou None en cas d'erreur
        """
        report_data = self.get_market_report()
        if not report_data:
            return None
        
        report = report_data.get('report', {})
        content = report.get('content', {})
        
        if format_type == "html":
            return content.get('html')
        elif format_type == "markdown":
            return content.get('markdown')
        else:
            logger.error(f"Format non supporté: {format_type}")
            return None
    
    def get_key_metrics(self) -> Optional[Dict[str, float]]:
        """
        Récupère les métriques clés du rapport
        
        Returns:
            Dictionnaire des métriques ou None en cas d'erreur
        """
        report_data = self.get_market_report()
        if not report_data:
            return None
        
        report = report_data.get('report', {})
        return report.get('key_metrics', {})
    
    def get_report_summary(self) -> Optional[Dict[str, Any]]:
        """
        Récupère le résumé du rapport
        
        Returns:
            Résumé du rapport ou None en cas d'erreur
        """
        report_data = self.get_market_report()
        if not report_data:
            return None
        
        report = report_data.get('report', {})
        return report.get('summary', {})
    
    def get_report_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les métadonnées du rapport
        
        Returns:
            Métadonnées du rapport ou None en cas d'erreur
        """
        report_data = self.get_market_report()
        if not report_data:
            return None
        
        report = report_data.get('report', {})
        return report.get('metadata', {})

class ManusStockAPI:
    """Classe pour interagir avec l'API de cours de bourse Manus"""
    
    def __init__(self, base_url: str = "https://ogh5izcelen1.manus.space"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InventorySBO/1.0 (Manus Integration)'
        })
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'une action
        
        Args:
            symbol: Symbole boursier (ex: AAPL, MSFT)
            
        Returns:
            Informations de l'action ou None en cas d'erreur
        """
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
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        # Essayer de parser comme JSON
                        try:
                            data = response.json()
                            logger.info(f"Données JSON récupérées pour {symbol}")
                            return data
                        except json.JSONDecodeError:
                            # Si ce n'est pas du JSON, c'est probablement du HTML
                            logger.info(f"Page HTML récupérée pour {symbol}")
                            return {
                                'symbol': symbol,
                                'format': 'html',
                                'content': response.text,
                                'url': f"{self.base_url}{endpoint}"
                            }
                    
                except Exception as e:
                    logger.debug(f"Erreur endpoint {endpoint}: {e}")
                    continue
            
            logger.error(f"Aucun endpoint fonctionnel trouvé pour {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données pour {symbol}: {e}")
            return None
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Récupère les informations de plusieurs actions
        
        Args:
            symbols: Liste des symboles boursiers
            
        Returns:
            Dictionnaire avec les données de chaque action
        """
        results = {}
        
        for symbol in symbols:
            logger.info(f"Récupération des données pour {symbol}...")
            data = self.get_stock_info(symbol)
            results[symbol] = data
            
            # Petite pause pour éviter de surcharger l'API
            import time
            time.sleep(0.5)
        
        return results
    
    def get_api_status(self) -> Optional[Dict[str, Any]]:
        """
        Vérifie le statut de l'API
        
        Returns:
            Informations de statut ou None en cas d'erreur
        """
        try:
            response = self.session.get(self.base_url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'status': 'online',
                    'response_time': response.elapsed.total_seconds(),
                    'content_type': response.headers.get('content-type'),
                    'url': self.base_url
                }
            else:
                return {
                    'status': 'error',
                    'status_code': response.status_code,
                    'url': self.base_url
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut: {e}")
            return None

class ManusIntegrationManager:
    """Gestionnaire principal pour l'intégration des APIs Manus"""
    
    def __init__(self):
        self.market_report_api = ManusMarketReportAPI()
        self.stock_api = ManusStockAPI()
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def get_market_update(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Récupère une mise à jour complète des marchés
        
        Args:
            force_refresh: Si True, force le rafraîchissement
            
        Returns:
            Mise à jour des marchés ou None en cas d'erreur
        """
        try:
            # Récupérer le rapport des marchés
            report_data = self.market_report_api.get_market_report(force_refresh)
            if not report_data:
                logger.error("Impossible de récupérer le rapport des marchés")
                return None
            
            # Extraire les informations importantes
            report = report_data.get('report', {})
            
            market_update = {
                'timestamp': datetime.now().isoformat(),
                'report_date': report.get('metadata', {}).get('report_date'),
                'summary': report.get('summary', {}),
                'key_metrics': report.get('key_metrics', {}),
                'content_markdown': report.get('content', {}).get('markdown'),
                'content_html': report.get('content', {}).get('html'),
                'sections': report.get('metadata', {}).get('sections', []),
                'api_info': report_data.get('api_info', {}),
                'cache_info': report_data.get('cache_info', {})
            }
            
            logger.info("Mise à jour des marchés récupérée avec succès")
            return market_update
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la mise à jour: {e}")
            return None
    
    def get_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Récupère les prix de plusieurs actions
        
        Args:
            symbols: Liste des symboles boursiers
            
        Returns:
            Dictionnaire avec les prix des actions
        """
        try:
            stock_data = self.stock_api.get_multiple_stocks(symbols)
            
            # Traiter les données
            processed_data = {}
            for symbol, data in stock_data.items():
                if data:
                    if data.get('format') == 'html':
                        # Pour les données HTML, on peut extraire des informations
                        processed_data[symbol] = {
                            'symbol': symbol,
                            'format': 'html',
                            'available': True,
                            'url': data.get('url'),
                            'content_length': len(data.get('content', ''))
                        }
                    else:
                        # Pour les données JSON
                        processed_data[symbol] = {
                            'symbol': symbol,
                            'format': 'json',
                            'available': True,
                            'data': data
                        }
                else:
                    processed_data[symbol] = {
                        'symbol': symbol,
                        'available': False,
                        'error': 'Données non disponibles'
                    }
            
            logger.info(f"Prix récupérés pour {len(symbols)} actions")
            return processed_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des prix: {e}")
            return {}
    
    def get_complete_market_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Récupère des données complètes du marché
        
        Args:
            symbols: Liste des symboles à surveiller (optionnel)
            
        Returns:
            Données complètes du marché
        """
        try:
            # Récupérer la mise à jour des marchés
            market_update = self.get_market_update()
            
            # Récupérer les prix des actions si des symboles sont fournis
            stock_prices = {}
            if symbols:
                stock_prices = self.get_stock_prices(symbols)
            
            # Vérifier le statut des APIs
            market_api_status = self.market_report_api.session.get(
                f"{self.market_report_api.base_url}/api/health",
                timeout=5
            ).status_code == 200 if market_update else False
            
            stock_api_status = self.stock_api.get_api_status()
            
            complete_data = {
                'timestamp': datetime.now().isoformat(),
                'market_update': market_update,
                'stock_prices': stock_prices,
                'api_status': {
                    'market_report_api': market_api_status,
                    'stock_api': stock_api_status
                },
                'summary': {
                    'market_data_available': market_update is not None,
                    'stocks_available': len([s for s in stock_prices.values() if s.get('available')]),
                    'total_stocks_requested': len(symbols) if symbols else 0
                }
            }
            
            logger.info("Données complètes du marché récupérées")
            return complete_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données complètes: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'market_update': None,
                'stock_prices': {},
                'api_status': {
                    'market_report_api': False,
                    'stock_api': False
                }
            }

# Fonctions utilitaires pour l'intégration dans l'application existante
def integrate_market_report_to_app() -> Optional[Dict[str, Any]]:
    """
    Fonction d'intégration pour récupérer les rapports de marché
    à utiliser dans votre application Flask
    """
    manager = ManusIntegrationManager()
    return manager.get_market_update()

def integrate_stock_prices_to_app(symbols: List[str]) -> Dict[str, Any]:
    """
    Fonction d'intégration pour récupérer les prix des actions
    à utiliser dans votre application Flask
    """
    manager = ManusIntegrationManager()
    return manager.get_stock_prices(symbols)

def get_complete_market_integration(symbols: List[str] = None) -> Dict[str, Any]:
    """
    Fonction d'intégration complète pour récupérer toutes les données
    à utiliser dans votre application Flask
    """
    manager = ManusIntegrationManager()
    return manager.get_complete_market_data(symbols)

# Exemple d'utilisation
if __name__ == "__main__":
    print("🧪 Test du module d'intégration Manus")
    print("=" * 50)
    
    # Test 1: Rapport des marchés
    print("\n📊 Test rapport des marchés...")
    market_update = integrate_market_report_to_app()
    if market_update:
        print("✅ Rapport des marchés récupéré")
        print(f"📅 Date: {market_update.get('report_date', 'N/A')}")
        print(f"📝 Sections: {len(market_update.get('sections', []))}")
    else:
        print("❌ Erreur rapport des marchés")
    
    # Test 2: Prix des actions
    print("\n💹 Test prix des actions...")
    symbols = ["AAPL", "MSFT", "GOOGL"]
    stock_prices = integrate_stock_prices_to_app(symbols)
    print(f"✅ Prix récupérés pour {len(symbols)} actions")
    
    for symbol, data in stock_prices.items():
        if data.get('available'):
            print(f"   📈 {symbol}: {data.get('format', 'N/A')}")
        else:
            print(f"   ❌ {symbol}: Non disponible")
    
    # Test 3: Données complètes
    print("\n🔗 Test données complètes...")
    complete_data = get_complete_market_integration(symbols)
    print("✅ Données complètes récupérées")
    print(f"📊 Résumé: {complete_data.get('summary', {})}")
    
    print("\n�� Tests terminés !") 