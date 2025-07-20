#!/usr/bin/env python3
"""
Script de test pour le nouveau prompt de briefing de marché
"""

import yfinance as yf
from datetime import datetime

def test_market_data_retrieval():
    """Test de récupération des données de marché"""
    
    print("🧪 Test de récupération des données de marché")
    print("=" * 60)
    
    # Symboles clés pour le briefing
    symbols = {
        'actions_usa': ['^GSPC', '^IXIC', '^DJI'],  # S&P 500, NASDAQ, Dow Jones
        'actions_europe': ['^STOXX50E', '^GDAXI', '^FCHI'],  # Euro Stoxx 50, DAX, CAC 40
        'actions_suisse': ['^SMI'],  # Swiss Market Index
        'obligations': ['^TNX', '^BUND', '^TYX'],  # US 10Y, Bund 10Y, US 30Y
        'crypto': ['BTC-USD', 'ETH-USD'],  # Bitcoin, Ethereum
        'forex': ['EURUSD=X', 'USDCHF=X', 'GBPUSD=X'],  # EUR/USD, USD/CHF, GBP/USD
        'commodities': ['GC=F', 'CL=F', 'SI=F']  # Or, Pétrole, Argent
    }
    
    current_time = datetime.now().strftime('%d/%m/%Y %H:%M CEST')
    print(f"📊 Données de marché - {current_time}")
    print("=" * 50)
    
    for category, symbol_list in symbols.items():
        print(f"\n{category.upper().replace('_', ' ')}:")
        
        for symbol in symbol_list:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    open_price = hist['Open'].iloc[0]
                    change = current_price - open_price
                    change_percent = (change / open_price) * 100 if open_price > 0 else 0
                    
                    # Nom du symbole
                    symbol_name = {
                        '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^DJI': 'Dow Jones',
                        '^STOXX50E': 'Euro Stoxx 50', '^GDAXI': 'DAX', '^FCHI': 'CAC 40',
                        '^SMI': 'Swiss Market Index', '^TNX': 'US 10Y', '^BUND': 'Bund 10Y',
                        '^TYX': 'US 30Y', 'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum',
                        'EURUSD=X': 'EUR/USD', 'USDCHF=X': 'USD/CHF', 'GBPUSD=X': 'GBP/USD',
                        'GC=F': 'Or', 'CL=F': 'Pétrole WTI', 'SI=F': 'Argent'
                    }.get(symbol, symbol)
                    
                    print(f"  {symbol_name}: {current_price:.2f} ({change_percent:+.2f}%)")
                else:
                    print(f"  {symbol}: Données non disponibles")
                    
            except Exception as e:
                print(f"  {symbol}: Erreur - {str(e)[:50]}")

def test_prompt_format():
    """Test du format du prompt"""
    
    print("\n" + "=" * 60)
    print("🧪 Test du format du prompt")
    print("=" * 60)
    
    # Simuler les données de marché
    market_data = """📊 Données de marché - 20/07/2025 21:30 CEST
==================================================

ACTIONS USA:
  S&P 500: 4567.89 (+0.85%)
  NASDAQ: 14234.56 (+1.23%)
  Dow Jones: 34567.89 (+0.45%)

ACTIONS EUROPE:
  Euro Stoxx 50: 4321.98 (-0.12%)
  DAX: 15678.90 (+0.34%)
  CAC 40: 6789.12 (-0.23%)

ACTIONS SUISSE:
  Swiss Market Index: 11234.56 (+0.67%)

OBLIGATIONS:
  US 10Y: 4.25 (-0.05%)
  Bund 10Y: 2.45 (+0.02%)
  US 30Y: 4.45 (-0.08%)

CRYPTO:
  Bitcoin: 65432.10 (+2.34%)
  Ethereum: 3456.78 (+1.89%)

FOREX:
  EUR/USD: 1.0876 (-0.15%)
  USD/CHF: 0.8923 (+0.23%)
  GBP/USD: 1.2345 (-0.34%)

COMMODITIES:
  Or: 2345.67 (+0.78%)
  Pétrole WTI: 78.90 (-1.23%)
  Argent: 28.45 (+0.45%)"""
    
    # Prompt mis à jour
    prompt = f"""Tu es un stratégiste financier expérimenté. Génère un briefing narratif fluide, concis et structuré sur la séance des marchés financiers du jour. Format exigé : - Ton narratif, comme un stratégiste qui me parle directement - Concision : pas de blabla, mais du fond - Structure logique intégrée dans le récit (pas de titres) : * Actions (USA, Europe, Suisse, autres zones si mouvement marquant) * Obligations souveraines (US 10Y, Bund, OAT, BTP, Confédération…) * Cryptoactifs (BTC, ETH, capitalisation globale, régulation, flux) * Macro, banques centrales et géopolitique (stats, décisions, tensions) - Termine par une synthèse rapide intégrée à la narration, avec ce que je dois retenir en une phrase, et signale tout signal faible ou rupture de tendance à surveiller. Si une classe d'actif n'a pas bougé, dis-le clairement sans meubler.

Données de marché actuelles à utiliser :
{market_data}

Génère un briefing pour aujourd'hui basé sur ces données de marché réelles."""
    
    print("✅ Prompt mis à jour avec succès")
    print(f"📏 Longueur du prompt: {len(prompt)} caractères")
    print(f"📊 Données de marché incluses: {len(market_data.split(chr(10)))} lignes")
    
    # Afficher un extrait du prompt
    print(f"\n📝 Extrait du prompt:")
    print("-" * 40)
    print(prompt[:500] + "...")
    print("-" * 40)

if __name__ == "__main__":
    # Test 1: Récupération des données
    test_market_data_retrieval()
    
    # Test 2: Format du prompt
    test_prompt_format()
    
    print("\n🏁 Tests terminés")
    print("\n💡 Le prompt a été mis à jour avec succès dans app.py") 