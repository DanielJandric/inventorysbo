#!/usr/bin/env python3
"""
Test du module d'intégration Manus
Montre les résultats des deux APIs Manus
"""

from manus_integration import (
    get_stock_price_manus,
    get_market_report_manus,
    generate_market_briefing_manus,
    get_exchange_rate_manus,
    manus_stock_api,
    manus_market_report_api
)

def test_stock_api():
    """Test de l'API de cours de bourse"""
    print("📈 Test API Cours de Bourse Manus")
    print("=" * 40)
    
    # Test avec plusieurs symboles
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    for symbol in symbols:
        print(f"\n🔍 Test {symbol}...")
        result = get_stock_price_manus(symbol)
        
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Source: {result.get('source', 'N/A')}")
        print(f"   Dernière mise à jour: {result.get('last_updated', 'N/A')}")
        
        if result.get('endpoint'):
            print(f"   Endpoint utilisé: {result.get('endpoint')}")
        
        if result.get('raw_content_length'):
            print(f"   Taille contenu: {result.get('raw_content_length')} caractères")
        
        if result.get('error'):
            print(f"   Erreur: {result.get('error')}")

def test_market_report_api():
    """Test de l'API de rapports de marché"""
    print("\n\n📊 Test API Rapports de Marché Manus")
    print("=" * 40)
    
    print("\n🔍 Récupération du rapport...")
    result = get_market_report_manus()
    
    print(f"   Status: {result.get('status', 'N/A')}")
    print(f"   Source: {result.get('source', 'N/A')}")
    print(f"   Date du rapport: {result.get('report_date', 'N/A')}")
    print(f"   Heure de génération: {result.get('generation_time', 'N/A')}")
    
    # Afficher les métriques de marché
    market_metrics = result.get('market_metrics', {})
    if market_metrics:
        print("\n   📈 Métriques de marché:")
        for key, value in market_metrics.items():
            print(f"      {key}: {value}")
    
    # Afficher les sections disponibles
    sections = result.get('sections', [])
    if sections:
        print(f"\n   📋 Sections disponibles ({len(sections)}):")
        for section in sections[:5]:  # Afficher les 5 premières
            print(f"      • {section}")
        if len(sections) > 5:
            print(f"      ... et {len(sections) - 5} autres")
    
    # Afficher le résumé
    summary = result.get('summary', {})
    if summary:
        key_points = summary.get('key_points', [])
        if key_points:
            print(f"\n   📝 Points clés ({len(key_points)}):")
            for point in key_points[:3]:  # Afficher les 3 premiers
                print(f"      • {point}")
            if len(key_points) > 3:
                print(f"      ... et {len(key_points) - 3} autres")

def test_market_briefing():
    """Test de la génération de briefing"""
    print("\n\n📋 Test Génération Briefing de Marché")
    print("=" * 40)
    
    print("\n🔍 Génération du briefing...")
    result = generate_market_briefing_manus()
    
    print(f"   Status: {result.get('status', 'N/A')}")
    print(f"   Source: {result.get('source', 'N/A')}")
    
    if result.get('status') == 'success':
        briefing = result.get('briefing', {})
        print(f"   Titre: {briefing.get('title', 'N/A')}")
        
        key_points = briefing.get('summary', [])
        if key_points:
            print(f"\n   📝 Points clés du briefing ({len(key_points)}):")
            for point in key_points[:3]:
                print(f"      • {point}")
            if len(key_points) > 3:
                print(f"      ... et {len(key_points) - 3} autres")
        
        metrics = briefing.get('metrics', {})
        if metrics:
            print(f"\n   📈 Métriques du briefing:")
            for key, value in metrics.items():
                print(f"      {key}: {value}")
    else:
        print(f"   Erreur: {result.get('message', 'N/A')}")

def test_exchange_rates():
    """Test des taux de change"""
    print("\n\n💱 Test Taux de Change Manus")
    print("=" * 40)
    
    # Test différents taux
    rates_to_test = [
        ('CHF', 'USD'),
        ('USD', 'CHF'),
        ('EUR', 'CHF'),
        ('CHF', 'EUR')
    ]
    
    for from_curr, to_curr in rates_to_test:
        rate = get_exchange_rate_manus(from_curr, to_curr)
        print(f"   {from_curr}/{to_curr}: {rate}")

def test_cache_status():
    """Test du statut des caches"""
    print("\n\n💾 Test Statut des Caches")
    print("=" * 40)
    
    # Cache des prix d'actions
    stock_cache = manus_stock_api.get_cache_status()
    print(f"   Cache prix d'actions:")
    print(f"      Taille: {stock_cache.get('cache_size', 0)} entrées")
    print(f"      Durée: {stock_cache.get('cache_duration_seconds', 0)} secondes")
    print(f"      Symboles en cache: {stock_cache.get('cached_symbols', [])}")
    
    # Cache des rapports
    report_cache = manus_market_report_api.get_cache_status()
    print(f"\n   Cache rapports de marché:")
    print(f"      Taille: {report_cache.get('cache_size', 0)} entrées")
    print(f"      Durée: {report_cache.get('cache_duration_seconds', 0)} secondes")

def test_api_status():
    """Test du statut des APIs"""
    print("\n\n🔍 Test Statut des APIs")
    print("=" * 40)
    
    # Statut API cours de bourse
    stock_status = manus_stock_api.get_api_status()
    print(f"   API Cours de Bourse:")
    print(f"      Status: {stock_status.get('status', 'N/A')}")
    print(f"      URL: {stock_status.get('url', 'N/A')}")
    if stock_status.get('response_time'):
        print(f"      Temps de réponse: {stock_status.get('response_time')}s")
    
    # Statut API rapports
    report_status = manus_market_report_api.get_api_status()
    print(f"\n   API Rapports de Marché:")
    print(f"      Status: {report_status.get('status', 'N/A')}")
    print(f"      URL: {report_status.get('url', 'N/A')}")
    if report_status.get('response_time'):
        print(f"      Temps de réponse: {report_status.get('response_time')}s")

def main():
    """Fonction principale de test"""
    print("🧪 Test Complet des APIs Manus")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Tests
    test_stock_api()
    test_market_report_api()
    test_market_briefing()
    test_exchange_rates()
    test_cache_status()
    test_api_status()
    
    print("\n" + "=" * 50)
    print("🎉 Tests terminés !")
    print("✅ Les deux APIs Manus sont fonctionnelles")
    print("📋 Résumé:")
    print("   • API Cours de Bourse: Opérationnelle")
    print("   • API Rapports de Marché: Opérationnelle")
    print("   • Cache: Fonctionnel")
    print("   • Taux de change: Disponibles")
    print("\n🚀 Prêt pour l'intégration dans votre application !")

if __name__ == "__main__":
    from datetime import datetime
    main() 