#!/usr/bin/env python3
"""
Script de test pour vérifier la correction de l'erreur 'errors'
"""

from stock_price_manager import StockPriceManager
import json

def test_update_all_stocks():
    """Test de la fonction update_all_stocks pour vérifier la structure des résultats"""
    
    print("🧪 Test de la structure des résultats update_all_stocks")
    print("=" * 60)
    
    # Initialiser le gestionnaire
    stock_manager = StockPriceManager()
    
    # Liste de symboles de test
    test_symbols = ["AAPL", "TSLA", "INVALID_SYMBOL"]
    
    print(f"📊 Symboles de test: {test_symbols}")
    
    # Test de mise à jour
    print("\n🔄 Début de la mise à jour...")
    results = stock_manager.update_all_stocks(test_symbols)
    
    # Vérifier la structure des résultats
    print(f"\n📋 Structure des résultats:")
    print(f"   Clés disponibles: {list(results.keys())}")
    
    # Vérifier que 'errors' n'existe pas
    if 'errors' in results:
        print(f"❌ ERREUR: La clé 'errors' existe encore!")
        return False
    else:
        print(f"✅ OK: La clé 'errors' n'existe pas")
    
    # Vérifier que 'failed' existe
    if 'failed' in results:
        print(f"✅ OK: La clé 'failed' existe")
    else:
        print(f"❌ ERREUR: La clé 'failed' manque!")
        return False
    
    # Afficher les détails
    print(f"\n📊 Détails des résultats:")
    print(f"   - Succès: {len(results['success'])}")
    print(f"   - Échecs: {len(results['failed'])}")
    print(f"   - Ignorés: {len(results['skipped'])}")
    print(f"   - Requêtes utilisées: {results.get('requests_used', 0)}")
    
    # Détails des succès
    if results['success']:
        print(f"\n✅ Actions mises à jour:")
        for item in results['success']:
            print(f"   - {item['symbol']}: {item['price']} {item['currency']}")
    
    # Détails des échecs
    if results['failed']:
        print(f"\n❌ Échecs:")
        for failed in results['failed']:
            print(f"   - {failed}")
    
    # Détails des ignorés
    if results['skipped']:
        print(f"\n⚠️ Ignorés:")
        for skipped in results['skipped']:
            print(f"   - {skipped}")
    
    print(f"\n✅ Test terminé avec succès!")
    return True

if __name__ == "__main__":
    test_update_all_stocks() 