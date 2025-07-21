#!/usr/bin/env python3
"""
Analyse des limitations actuelles dans la transmission des données Manus à ChatGPT
"""

import json

def test_limitations_actuelles():
    """Test des limitations actuelles dans le code"""
    
    print("🔍 Analyse des limitations actuelles dans la transmission des données Manus...")
    
    # Données d'exemple pour simuler l'API Manus
    sample_financial_data = {
        "financial_data": {
            "markets": {
                "S&P 500": {"price": 4500.25, "change": 25.50, "change_percent": 0.57},
                "NASDAQ": {"price": 14250.75, "change": -15.25, "change_percent": -0.11},
                "DOW": {"price": 34500.00, "change": 125.75, "change_percent": 0.37},
                "FTSE 100": {"price": 7500.50, "change": 45.25, "change_percent": 0.61},
                "DAX": {"price": 15800.25, "change": 75.50, "change_percent": 0.48},
                "CAC 40": {"price": 7200.75, "change": 35.25, "change_percent": 0.49},
                "SMI": {"price": 11250.00, "change": 125.75, "change_percent": 1.13},
                "NIKKEI 225": {"price": 32500.50, "change": -250.25, "change_percent": -0.76}
            },
            "bonds": [
                {"name": "US 10Y Treasury", "yield": 4.25, "change": 0.05},
                {"name": "German 10Y Bund", "yield": 2.15, "change": -0.02},
                {"name": "French 10Y OAT", "yield": 2.85, "change": 0.01},
                {"name": "Italian 10Y BTP", "yield": 4.45, "change": 0.08},
                {"name": "Swiss 10Y Confederation", "yield": 1.25, "change": 0.03}
            ],
            "commodities": [
                {"name": "Brent Crude", "price": 85.50, "change": 1.25},
                {"name": "WTI Crude", "price": 82.75, "change": 1.15},
                {"name": "Gold", "price": 1950.00, "change": 15.50},
                {"name": "Silver", "price": 24.50, "change": 0.35},
                {"name": "Copper", "price": 3.85, "change": 0.05}
            ],
            "currencies": [
                {"pair": "EUR/USD", "rate": 1.0850, "change": 0.0025},
                {"pair": "GBP/USD", "rate": 1.2650, "change": -0.0050},
                {"pair": "USD/JPY", "rate": 148.50, "change": 0.75},
                {"pair": "USD/CHF", "rate": 0.8850, "change": -0.0025},
                {"pair": "EUR/CHF", "rate": 0.9600, "change": 0.0010}
            ]
        },
        "crypto_data": {
            "cryptocurrencies": [
                {"name": "Bitcoin", "price": 43500, "change": 1250, "market_cap": 850000000000},
                {"name": "Ethereum", "price": 2650, "change": 75, "market_cap": 320000000000},
                {"name": "BNB", "price": 315, "change": 8, "market_cap": 48000000000},
                {"name": "XRP", "price": 0.58, "change": 0.02, "market_cap": 31000000000},
                {"name": "Cardano", "price": 0.45, "change": 0.03, "market_cap": 16000000000}
            ]
        }
    }
    
    sample_economic_data = {
        "economic_data": {
            "indicators": {
                "US_CPI": {"value": 3.2, "previous": 3.1, "change": 0.1},
                "US_Unemployment": {"value": 3.8, "previous": 3.9, "change": -0.1},
                "US_PMI_Manufacturing": {"value": 48.5, "previous": 47.8, "change": 0.7},
                "US_PMI_Services": {"value": 52.5, "previous": 51.8, "change": 0.7},
                "EU_CPI": {"value": 2.8, "previous": 2.9, "change": -0.1},
                "EU_Unemployment": {"value": 6.5, "previous": 6.6, "change": -0.1},
                "CH_CPI": {"value": 1.8, "previous": 1.7, "change": 0.1},
                "CH_Unemployment": {"value": 2.1, "previous": 2.2, "change": -0.1}
            }
        }
    }
    
    sample_news_data = {
        "news_data": {
            "Fed_Meeting": {"title": "Fed maintient les taux, signale patience", "impact": "high"},
            "ECB_Decision": {"title": "BCE envisage une pause dans les hausses", "impact": "high"},
            "Trade_War": {"title": "Tensions commerciales USA-Chine s'intensifient", "impact": "medium"},
            "Oil_Supply": {"title": "OPEC+ annonce de nouvelles réductions", "impact": "high"},
            "Tech_Earnings": {"title": "Résultats tech dépassent les attentes", "impact": "medium"},
            "Swiss_Banking": {"title": "UBS annonce de nouveaux objectifs", "impact": "low"},
            "Crypto_Regulation": {"title": "Nouvelles règles crypto en Europe", "impact": "medium"},
            "Climate_Finance": {"title": "Investissements verts en hausse", "impact": "low"}
        }
    }
    
    # Extraire les données
    markets = sample_financial_data["financial_data"]["markets"]
    bonds = sample_financial_data["financial_data"]["bonds"]
    cryptos = sample_financial_data["crypto_data"]["cryptocurrencies"]
    commodities = sample_financial_data["financial_data"]["commodities"]
    currencies = sample_financial_data["financial_data"]["currencies"]
    indicators = sample_economic_data["economic_data"]["indicators"]
    news = sample_news_data["news_data"]
    
    # Convertir en JSON
    markets_json = json.dumps(markets, indent=2, ensure_ascii=False)
    bonds_json = json.dumps(bonds, indent=2, ensure_ascii=False)
    cryptos_json = json.dumps(cryptos, indent=2, ensure_ascii=False)
    commodities_json = json.dumps(commodities, indent=2, ensure_ascii=False)
    currencies_json = json.dumps(currencies, indent=2, ensure_ascii=False)
    indicators_json = json.dumps(indicators, indent=2, ensure_ascii=False)
    news_json = json.dumps(news, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("📊 ANALYSE DES DONNÉES D'EXEMPLE")
    print("="*80)
    
    print(f"📈 Marchés financiers: {len(markets)} indices")
    print(f"📊 Obligations: {len(bonds)} obligations")
    print(f"🪙 Cryptomonnaies: {len(cryptos)} cryptos")
    print(f"🛢️ Commodités: {len(commodities)} commodités")
    print(f"💱 Devises: {len(currencies)} paires")
    print(f"📊 Indicateurs économiques: {len(indicators)} indicateurs")
    print(f"📰 Actualités: {len(news)} articles")
    
    print("\n" + "="*80)
    print("⚠️ LIMITATIONS ACTUELLES DANS LE CODE")
    print("="*80)
    
    print(f"📈 Marchés financiers:")
    print(f"   - Données complètes: {len(markets_json)} caractères")
    print(f"   - Limitation actuelle: 1000 caractères")
    print(f"   - Données perdues: {max(0, len(markets_json) - 1000)} caractères")
    print(f"   - Pourcentage perdu: {max(0, (len(markets_json) - 1000) / len(markets_json) * 100):.1f}%")
    
    print(f"📊 Obligations:")
    print(f"   - Données complètes: {len(bonds_json)} caractères")
    print(f"   - Limitation actuelle: 500 caractères")
    print(f"   - Données perdues: {max(0, len(bonds_json) - 500)} caractères")
    print(f"   - Pourcentage perdu: {max(0, (len(bonds_json) - 500) / len(bonds_json) * 100):.1f}%")
    
    print(f"🪙 Cryptomonnaies:")
    print(f"   - Données complètes: {len(cryptos_json)} caractères")
    print(f"   - Limitation actuelle: 500 caractères")
    print(f"   - Données perdues: {max(0, len(cryptos_json) - 500)} caractères")
    print(f"   - Pourcentage perdu: {max(0, (len(cryptos_json) - 500) / len(cryptos_json) * 100):.1f}%")
    
    print(f"🛢️ Commodités:")
    print(f"   - Données complètes: {len(commodities_json)} caractères")
    print(f"   - Limitation actuelle: 500 caractères")
    print(f"   - Données perdues: {max(0, len(commodities_json) - 500)} caractères")
    print(f"   - Pourcentage perdu: {max(0, (len(commodities_json) - 500) / len(commodities_json) * 100):.1f}%")
    
    print(f"💱 Devises:")
    print(f"   - Données complètes: {len(currencies_json)} caractères")
    print(f"   - Limitation actuelle: 500 caractères")
    print(f"   - Données perdues: {max(0, len(currencies_json) - 500)} caractères")
    print(f"   - Pourcentage perdu: {max(0, (len(currencies_json) - 500) / len(currencies_json) * 100):.1f}%")
    
    print(f"📊 Indicateurs économiques:")
    print(f"   - Données complètes: {len(indicators_json)} caractères")
    print(f"   - Limitation actuelle: 1000 caractères")
    print(f"   - Données perdues: {max(0, len(indicators_json) - 1000)} caractères")
    print(f"   - Pourcentage perdu: {max(0, (len(indicators_json) - 1000) / len(indicators_json) * 100):.1f}%")
    
    print(f"📰 Actualités:")
    print(f"   - Données complètes: {len(news_json)} caractères")
    print(f"   - Limitation actuelle: 1000 caractères")
    print(f"   - Données perdues: {max(0, len(news_json) - 1000)} caractères")
    print(f"   - Pourcentage perdu: {max(0, (len(news_json) - 1000) / len(news_json) * 100):.1f}%")
    
    # Construire les contextes
    context_limited = f"""Données de marché actuelles (API Manus):

MARCHÉS FINANCIERS:
{markets_json[:1000]}

OBLIGATIONS:
{bonds_json[:500]}

CRYPTOMONNAIES:
{cryptos_json[:500]}

COMMODITÉS:
{commodities_json[:500]}

DEVISES:
{currencies_json[:500]}

INDICATEURS ÉCONOMIQUES:
{indicators_json[:1000]}

ACTUALITÉS:
{news_json[:1000]}"""

    context_complete = f"""Données de marché actuelles (API Manus):

MARCHÉS FINANCIERS:
{markets_json}

OBLIGATIONS:
{bonds_json}

CRYPTOMONNAIES:
{cryptos_json}

COMMODITÉS:
{commodities_json}

DEVISES:
{currencies_json}

INDICATEURS ÉCONOMIQUES:
{indicators_json}

ACTUALITÉS:
{news_json}"""

    print("\n" + "="*80)
    print("📏 COMPARAISON DES TAILLES DE CONTEXTE")
    print("="*80)
    
    print(f"Contexte avec limitations: {len(context_limited)} caractères")
    print(f"Contexte complet: {len(context_complete)} caractères")
    print(f"Données perdues: {len(context_complete) - len(context_limited)} caractères")
    print(f"Pourcentage perdu: {((len(context_complete) - len(context_limited)) / len(context_complete) * 100):.1f}%")
    
    # Estimation des tokens
    tokens_limited = len(context_limited) // 4
    tokens_complete = len(context_complete) // 4
    
    print("\n" + "="*80)
    print("🤖 LIMITES OPENAI GPT-4o")
    print("="*80)
    
    print(f"Tokens estimés (contexte limité): {tokens_limited}")
    print(f"Tokens estimés (contexte complet): {tokens_complete}")
    print(f"Limite GPT-4o: 128,000 tokens")
    print(f"Marge disponible: {128000 - tokens_complete}")
    
    print("\n" + "="*80)
    print("💡 RECOMMANDATIONS")
    print("="*80)
    
    if tokens_complete < 100000:
        print("✅ SUPPRIMER LES LIMITATIONS")
        print("   - Les données complètes peuvent être transmises")
        print("   - Plus d'informations pour ChatGPT")
        print("   - Analyse plus complète et précise")
        print("   - Pas de perte d'informations importantes")
    else:
        print("⚠️ OPTIMISER LES DONNÉES")
        print("   - Filtrer les données les plus importantes")
        print("   - Structurer les données de manière plus concise")
        print("   - Prioriser les informations clés")
    
    print("\n" + "="*80)
    print("🔧 SOLUTION PROPOSÉE")
    print("="*80)
    
    print("Modifier le code dans app.py pour supprimer les limitations :")
    print("1. Remplacer [:1000] et [:500] par les données complètes")
    print("2. Garder la structure JSON pour la lisibilité")
    print("3. Augmenter max_tokens si nécessaire")
    print("4. Tester avec les vraies données Manus")
    
    print("\n✅ Analyse terminée !")

if __name__ == "__main__":
    test_limitations_actuelles() 