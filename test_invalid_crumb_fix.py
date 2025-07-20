#!/usr/bin/env python3
"""
Script de test pour la correction de l'erreur "Invalid Crumb" Yahoo Finance
"""

import yfinance as yf
import time
import json

def test_yahoo_finance_direct():
    """Test direct de Yahoo Finance pour reproduire l'erreur"""
    
    print("🧪 Test direct Yahoo Finance")
    print("=" * 50)
    
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in test_symbols:
        print(f"\n📊 Test du symbole: {symbol}")
        print("-" * 30)
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Test 1: Récupération des infos
            print("1️⃣ Récupération des infos...")
            info = ticker.info
            print(f"   ✅ Infos récupérées: {info.get('shortName', 'N/A')}")
            
            # Test 2: Récupération de l'historique
            print("2️⃣ Récupération de l'historique...")
            hist = ticker.history(period="1d")
            if not hist.empty:
                print(f"   ✅ Historique récupéré: {len(hist)} entrées")
                print(f"   💰 Prix: {hist['Close'].iloc[-1]:.2f}")
            else:
                print("   ❌ Historique vide")
            
            # Test 3: Récupération des métriques
            print("3️⃣ Récupération des métriques...")
            try:
                # Essayer d'accéder à des métriques spécifiques
                market_cap = info.get('marketCap')
                pe_ratio = info.get('trailingPE')
                print(f"   💼 Market Cap: {market_cap}")
                print(f"   📊 P/E Ratio: {pe_ratio}")
            except Exception as e:
                print(f"   ⚠️ Erreur métriques: {e}")
            
        except Exception as e:
            error_str = str(e)
            print(f"   ❌ Erreur: {error_str}")
            
            if "Invalid Crumb" in error_str:
                print("   🔧 Erreur Invalid Crumb détectée!")
                print("   ⏳ Attente de 3 secondes...")
                time.sleep(3)
                
                try:
                    print("   🔄 Nouvelle tentative...")
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    hist = ticker.history(period="1d")
                    print(f"   ✅ Succès après retry: {hist['Close'].iloc[-1]:.2f}")
                except Exception as retry_error:
                    print(f"   ❌ Échec du retry: {retry_error}")
            
            elif "Unauthorized" in error_str:
                print("   🔧 Erreur Unauthorized détectée!")
            else:
                print("   🔧 Autre type d'erreur")

def test_stock_manager_with_retry():
    """Test du gestionnaire avec retry"""
    
    print("\n" + "=" * 50)
    print("🧪 Test du gestionnaire avec retry")
    print("=" * 50)
    
    from stock_price_manager import StockPriceManager
    
    stock_manager = StockPriceManager()
    
    # Réinitialiser le compteur pour le test
    stock_manager.reset_daily_requests()
    
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in test_symbols:
        print(f"\n📊 Test du symbole: {symbol}")
        print("-" * 30)
        
        price_data = stock_manager.get_stock_price(symbol)
        
        if price_data:
            print(f"   ✅ Prix récupéré: {price_data.price} {price_data.currency}")
            print(f"   📈 Variation: {price_data.change:.2f} ({price_data.change_percent:.2f}%)")
            print(f"   📊 Volume: {price_data.volume}")
        else:
            print(f"   ❌ Échec de récupération")
    
    # Afficher le statut final
    status = stock_manager.get_daily_requests_status()
    print(f"\n📊 Statut final: {status}")

def test_multiple_requests():
    """Test de plusieurs requêtes consécutives"""
    
    print("\n" + "=" * 50)
    print("🧪 Test de plusieurs requêtes consécutives")
    print("=" * 50)
    
    from stock_price_manager import StockPriceManager
    
    stock_manager = StockPriceManager()
    
    # Réinitialiser le compteur
    stock_manager.reset_daily_requests()
    
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    print(f"📊 Test de {len(symbols)} symboles consécutifs...")
    
    results = stock_manager.update_all_stocks(symbols)
    
    print(f"\n✅ Résultats:")
    print(f"   - Succès: {len(results['success'])}")
    print(f"   - Erreurs: {len(results['errors'])}")
    print(f"   - Requêtes utilisées: {results['requests_used']}")
    
    if results['errors']:
        print(f"\n❌ Erreurs détectées:")
        for error in results['errors']:
            print(f"   - {error['symbol']}: {error.get('reason', 'Erreur inconnue')}")

if __name__ == "__main__":
    # Test 1: Yahoo Finance direct
    test_yahoo_finance_direct()
    
    # Test 2: Gestionnaire avec retry
    test_stock_manager_with_retry()
    
    # Test 3: Requêtes multiples
    test_multiple_requests()
    
    print("\n�� Tests terminés") 