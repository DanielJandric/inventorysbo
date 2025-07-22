#!/usr/bin/env python3
"""
Diagnostic : Pourquoi ça fonctionne en local mais pas dans la webapp
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_environment_differences():
    """Test des différences d'environnement"""
    print("🔍 Test des différences d'environnement...")
    
    # Vérifier les variables d'environnement
    print("\n📋 Variables d'environnement:")
    env_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY', 
        'YAHOO_FINANCE_API_KEY',
        'MANUS_API_KEY',
        'FLASK_ENV',
        'PYTHONPATH'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ✅ {var}: {'*' * len(value)} (longueur: {len(value)})")
        else:
            print(f"   ❌ {var}: Non définie")
    
    # Vérifier les packages installés
    print("\n📦 Packages installés:")
    try:
        import yfinance
        print(f"   ✅ yfinance: {yfinance.__version__}")
    except ImportError:
        print(f"   ❌ yfinance: Non installé")
    
    try:
        import requests
        print(f"   ✅ requests: {requests.__version__}")
    except ImportError:
        print(f"   ❌ requests: Non installé")
    
    try:
        import httpx
        print(f"   ✅ httpx: {httpx.__version__}")
    except ImportError:
        print(f"   ❌ httpx: Non installé")

def test_network_access():
    """Test de l'accès réseau"""
    print("\n🌐 Test de l'accès réseau...")
    
    import requests
    
    # Test yfinance
    try:
        print("   🔗 Test yfinance:")
        response = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/AAPL", timeout=10)
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            print(f"      ✅ Accès yfinance OK")
        else:
            print(f"      ❌ Accès yfinance échoué")
    except Exception as e:
        print(f"      ❌ Erreur yfinance: {e}")
    
    # Test Manus API
    try:
        print("   🔗 Test Manus API:")
        response = requests.get("https://ogh5izcelen1.manus.space/api/stocks/AAPL", timeout=10)
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            print(f"      ✅ Accès Manus OK")
        else:
            print(f"      ❌ Accès Manus échoué")
    except Exception as e:
        print(f"      ❌ Erreur Manus: {e}")

def test_local_vs_webapp_logic():
    """Test de la logique locale vs webapp"""
    print("\n🔍 Test de la logique locale vs webapp...")
    
    try:
        from manus_integration import manus_stock_api
        
        # Test direct (comme en local)
        print("   📈 Test direct (local):")
        result_local = manus_stock_api.get_stock_price("AAPL", force_refresh=True)
        print(f"      Prix: {result_local.get('price')} {result_local.get('currency')}")
        print(f"      Source: {result_local.get('source')}")
        print(f"      Status: {result_local.get('status')}")
        
        # Simuler les conditions webapp
        print("   🌐 Test conditions webapp:")
        
        # Vider le cache pour simuler un nouvel environnement
        manus_stock_api.clear_cache()
        
        # Test avec cache vide (comme au démarrage webapp)
        result_webapp = manus_stock_api.get_stock_price("AAPL", force_refresh=False)
        print(f"      Prix: {result_webapp.get('price')} {result_webapp.get('currency')}")
        print(f"      Source: {result_webapp.get('source')}")
        print(f"      Status: {result_webapp.get('status')}")
        
        # Comparer
        if result_local.get('price') == result_webapp.get('price'):
            print(f"      ✅ Résultats identiques")
        else:
            print(f"      ❌ Résultats différents!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur test: {e}")
        return False

def test_app_integration():
    """Test de l'intégration dans app.py"""
    print("\n🔍 Test de l'intégration dans app.py...")
    
    try:
        # Importer les fonctions de app.py
        from app import get_stock_price_manus
        
        print("   📈 Test via app.py:")
        
        # Test avec les paramètres de app.py
        result = get_stock_price_manus("AAPL", force_refresh=True)
        
        print(f"      Prix: {result.get('price')} {result.get('currency')}")
        print(f"      Source: {result.get('source')}")
        print(f"      Status: {result.get('status')}")
        
        if result.get('price') == 1.0:
            print(f"      ⚠️ Prix à 1.0 (problème webapp)")
        else:
            print(f"      ✅ Prix correct")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur app.py: {e}")
        return False

def check_requirements_txt():
    """Vérifier requirements.txt"""
    print("\n📋 Vérification requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        print("   📦 Packages requis:")
        for line in requirements.split('\n'):
            if line.strip() and not line.startswith('#'):
                print(f"      {line.strip()}")
        
        # Vérifier si yfinance est dans requirements.txt
        if 'yfinance' in requirements:
            print(f"   ✅ yfinance dans requirements.txt")
        else:
            print(f"   ❌ yfinance manquant dans requirements.txt")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur lecture requirements.txt: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Diagnostic : Local vs Webapp")
    print("=" * 80)
    
    # Test environnement
    test_environment_differences()
    
    # Test réseau
    test_network_access()
    
    # Test logique
    test_local_vs_webapp_logic()
    
    # Test app.py
    test_app_integration()
    
    # Vérifier requirements.txt
    check_requirements_txt()
    
    print("\n" + "=" * 80)
    print("📋 HYPOTHÈSES POSSIBLES:")
    print("1. yfinance non installé sur Render")
    print("2. Variables d'environnement manquantes")
    print("3. Cache différent entre local et production")
    print("4. Logique d'intégration différente dans app.py")
    print("5. Restrictions réseau sur Render")
    print("6. Version Python différente")

if __name__ == "__main__":
    main() 