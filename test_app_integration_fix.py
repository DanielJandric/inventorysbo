#!/usr/bin/env python3
"""
Test et correction de l'intégration dans app.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_app_integration_without_supabase():
    """Test de l'intégration sans Supabase"""
    print("🔍 Test de l'intégration sans Supabase...")
    
    try:
        # Simuler les variables d'environnement manquantes
        original_supabase_url = os.environ.get('SUPABASE_URL')
        original_supabase_key = os.environ.get('SUPABASE_KEY')
        
        # Supprimer temporairement les variables
        if 'SUPABASE_URL' in os.environ:
            del os.environ['SUPABASE_URL']
        if 'SUPABASE_KEY' in os.environ:
            del os.environ['SUPABASE_KEY']
        
        print("   🔧 Variables Supabase temporairement supprimées")
        
        # Test direct de manus_integration
        print("   📈 Test direct manus_integration:")
        from manus_integration import manus_stock_api
        
        result = manus_stock_api.get_stock_price("AAPL", force_refresh=True)
        print(f"      Prix: {result.get('price')} {result.get('currency')}")
        print(f"      Source: {result.get('source')}")
        print(f"      Status: {result.get('status')}")
        
        # Restaurer les variables
        if original_supabase_url:
            os.environ['SUPABASE_URL'] = original_supabase_url
        if original_supabase_key:
            os.environ['SUPABASE_KEY'] = original_supabase_key
        
        return result.get('price') != 1.0
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_app_route_logic():
    """Test de la logique des routes app.py"""
    print("\n🔍 Test de la logique des routes...")
    
    try:
        # Importer les fonctions nécessaires
        from manus_integration import manus_stock_api
        
        # Simuler la logique de la route /api/stock-price/<symbol>
        symbol = "AAPL"
        force_refresh = True
        
        print(f"   📈 Test route pour {symbol}:")
        
        # Logique de la route
        try:
            # Appel direct à manus_integration
            stock_data = manus_stock_api.get_stock_price(symbol, force_refresh=force_refresh)
            
            # Vérifier si on a des données
            if stock_data and stock_data.get('price'):
                print(f"      ✅ Données obtenues: {stock_data.get('price')} {stock_data.get('currency')}")
                print(f"      📋 Source: {stock_data.get('source')}")
                
                # Simuler la réponse JSON
                response_data = {
                    'success': True,
                    'data': stock_data,
                    'timestamp': stock_data.get('last_updated'),
                    'source': stock_data.get('source')
                }
                
                print(f"      📄 Réponse JSON simulée: {response_data['success']}")
                return True
            else:
                print(f"      ❌ Aucune donnée obtenue")
                return False
                
        except Exception as e:
            print(f"      ❌ Erreur route: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Erreur test route: {e}")
        return False

def test_rate_limiting_handling():
    """Test de la gestion du rate limiting"""
    print("\n🔍 Test de la gestion du rate limiting...")
    
    try:
        from manus_integration import manus_stock_api
        
        symbols = ["AAPL", "TSLA", "IREN.SW"]
        
        print("   📈 Test avec plusieurs symboles:")
        
        results = []
        for i, symbol in enumerate(symbols):
            print(f"      {i+1}. {symbol}:")
            
            # Vider le cache
            manus_stock_api.clear_cache()
            
            # Test avec délai
            import time
            if i > 0:
                print(f"         ⏳ Attente 3s...")
                time.sleep(3)
            
            result = manus_stock_api.get_stock_price(symbol, force_refresh=True)
            price = result.get('price')
            source = result.get('source')
            
            print(f"         💰 Prix: {price} {result.get('currency')}")
            print(f"         📋 Source: {source}")
            
            if price == 1.0:
                print(f"         ⚠️ Prix à 1.0 (possible rate limiting)")
                results.append(False)
            else:
                print(f"         ✅ Prix correct")
                results.append(True)
        
        success_rate = sum(results) / len(results)
        print(f"   📊 Taux de succès: {success_rate:.1%}")
        
        return success_rate > 0.5
        
    except Exception as e:
        print(f"   ❌ Erreur test rate limiting: {e}")
        return False

def suggest_fixes():
    """Suggestions de corrections"""
    print("\n💡 SUGGESTIONS DE CORRECTIONS:")
    
    suggestions = [
        "1. Mettre à jour requirements.txt avec yfinance>=0.2.65",
        "2. Ajouter httpx>=0.28.0 dans requirements.txt",
        "3. Améliorer la gestion des erreurs 429 dans app.py",
        "4. Ajouter des délais entre les requêtes dans les routes",
        "5. Implémenter un cache global pour éviter les requêtes répétées",
        "6. Ajouter des logs détaillés pour tracer les erreurs en production",
        "7. Vérifier que Render installe bien yfinance",
        "8. Ajouter une route de test pour vérifier l'installation des packages"
    ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")

def main():
    """Test principal"""
    print("🚀 Test et correction de l'intégration app.py")
    print("=" * 80)
    
    # Test sans Supabase
    test1 = test_app_integration_without_supabase()
    
    # Test routes
    test2 = test_app_route_logic()
    
    # Test rate limiting
    test3 = test_rate_limiting_handling()
    
    # Suggestions
    suggest_fixes()
    
    print("\n" + "=" * 80)
    print("📋 RÉSULTATS:")
    print(f"✅ Test sans Supabase: {'PASSÉ' if test1 else 'ÉCHOUÉ'}")
    print(f"✅ Test routes: {'PASSÉ' if test2 else 'ÉCHOUÉ'}")
    print(f"✅ Test rate limiting: {'PASSÉ' if test3 else 'ÉCHOUÉ'}")
    
    if all([test1, test2, test3]):
        print("🎉 TOUS LES TESTS PASSÉS!")
    else:
        print("⚠️ Certains tests ont échoué - corrections nécessaires")

if __name__ == "__main__":
    main() 