#!/usr/bin/env python3
"""
Test de transmission des données Manus à ChatGPT
Vérification de la qualité et de la quantité des données transmises
"""

import json
import requests
from datetime import datetime

# Configuration
MANUS_API_BASE_URL = "https://e5h6i7cn86z0.manus.space"

def test_manus_data_transmission():
    """Test de la transmission des données Manus"""
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    print("🔍 Test de transmission des données Manus à ChatGPT...")
    
    try:
        # 1. Collecter les données via API Manus
        print("1. Collecte des données Manus...")
        collect_response = requests.post(f"{MANUS_API_BASE_URL}/api/data/collect", timeout=30)
        if collect_response.status_code != 200:
            print(f"❌ Erreur collecte données Manus: {collect_response.status_code}")
            return
        print("✅ Données collectées")
        
        # 2. Récupérer les données détaillées
        print("2. Récupération des données détaillées...")
        financial_response = requests.get(f"{MANUS_API_BASE_URL}/api/data/financial", timeout=30)
        financial_data = financial_response.json() if financial_response.status_code == 200 else {}
        
        economic_response = requests.get(f"{MANUS_API_BASE_URL}/api/data/economic", timeout=30)
        economic_data = economic_response.json() if economic_response.status_code == 200 else {}
        
        news_response = requests.get(f"{MANUS_API_BASE_URL}/api/data/news", timeout=30)
        news_data = news_response.json() if news_response.status_code == 200 else {}
        
        print("✅ Données détaillées récupérées")
        
        # 3. Analyser les données brutes
        print("\n" + "="*80)
        print("📊 ANALYSE DES DONNÉES BRUTES MANUS")
        print("="*80)
        
        # Marchés financiers
        markets = financial_data.get('financial_data', {}).get('markets', {})
        print(f"📈 Marchés financiers: {len(markets)} indices")
        if markets:
            print("   Exemples d'indices:")
            for i, (key, value) in enumerate(list(markets.items())[:5]):
                print(f"   - {key}: {value}")
        
        # Obligations
        bonds = financial_data.get('financial_data', {}).get('bonds', [])
        print(f"📊 Obligations: {len(bonds)} obligations")
        if bonds:
            print("   Exemples d'obligations:")
            for i, bond in enumerate(bonds[:3]):
                print(f"   - {bond}")
        
        # Cryptomonnaies
        cryptos = financial_data.get('crypto_data', {}).get('cryptocurrencies', [])
        print(f"🪙 Cryptomonnaies: {len(cryptos)} cryptos")
        if cryptos:
            print("   Exemples de cryptos:")
            for i, crypto in enumerate(cryptos[:3]):
                print(f"   - {crypto}")
        
        # Commodités
        commodities = financial_data.get('financial_data', {}).get('commodities', [])
        print(f"🛢️ Commodités: {len(commodities)} commodités")
        if commodities:
            print("   Exemples de commodités:")
            for i, commodity in enumerate(commodities[:3]):
                print(f"   - {commodity}")
        
        # Devises
        currencies = financial_data.get('financial_data', {}).get('currencies', [])
        print(f"💱 Devises: {len(currencies)} paires")
        if currencies:
            print("   Exemples de devises:")
            for i, currency in enumerate(currencies[:3]):
                print(f"   - {currency}")
        
        # Indicateurs économiques
        indicators = economic_data.get('economic_data', {}).get('indicators', {})
        print(f"📊 Indicateurs économiques: {len(indicators)} indicateurs")
        if indicators:
            print("   Exemples d'indicateurs:")
            for i, (key, value) in enumerate(list(indicators.items())[:3]):
                print(f"   - {key}: {value}")
        
        # Actualités
        news = news_data.get('news_data', {})
        print(f"📰 Actualités: {len(news)} articles")
        if news:
            print("   Exemples d'actualités:")
            for i, (key, value) in enumerate(list(news.items())[:3]):
                print(f"   - {key}: {value}")
        
        # 4. Analyser les limitations actuelles
        print("\n" + "="*80)
        print("⚠️ LIMITATIONS ACTUELLES DANS LE CODE")
        print("="*80)
        
        # Calculer les tailles des données
        markets_json = json.dumps(markets, indent=2, ensure_ascii=False)
        bonds_json = json.dumps(bonds, indent=2, ensure_ascii=False)
        cryptos_json = json.dumps(cryptos, indent=2, ensure_ascii=False)
        commodities_json = json.dumps(commodities, indent=2, ensure_ascii=False)
        currencies_json = json.dumps(currencies, indent=2, ensure_ascii=False)
        indicators_json = json.dumps(indicators, indent=2, ensure_ascii=False)
        news_json = json.dumps(news, indent=2, ensure_ascii=False)
        
        print(f"📈 Marchés financiers:")
        print(f"   - Données complètes: {len(markets_json)} caractères")
        print(f"   - Limitation actuelle: 1000 caractères")
        print(f"   - Données perdues: {max(0, len(markets_json) - 1000)} caractères")
        
        print(f"📊 Obligations:")
        print(f"   - Données complètes: {len(bonds_json)} caractères")
        print(f"   - Limitation actuelle: 500 caractères")
        print(f"   - Données perdues: {max(0, len(bonds_json) - 500)} caractères")
        
        print(f"🪙 Cryptomonnaies:")
        print(f"   - Données complètes: {len(cryptos_json)} caractères")
        print(f"   - Limitation actuelle: 500 caractères")
        print(f"   - Données perdues: {max(0, len(cryptos_json) - 500)} caractères")
        
        print(f"🛢️ Commodités:")
        print(f"   - Données complètes: {len(commodities_json)} caractères")
        print(f"   - Limitation actuelle: 500 caractères")
        print(f"   - Données perdues: {max(0, len(commodities_json) - 500)} caractères")
        
        print(f"💱 Devises:")
        print(f"   - Données complètes: {len(currencies_json)} caractères")
        print(f"   - Limitation actuelle: 500 caractères")
        print(f"   - Données perdues: {max(0, len(currencies_json) - 500)} caractères")
        
        print(f"📊 Indicateurs économiques:")
        print(f"   - Données complètes: {len(indicators_json)} caractères")
        print(f"   - Limitation actuelle: 1000 caractères")
        print(f"   - Données perdues: {max(0, len(indicators_json) - 1000)} caractères")
        
        print(f"📰 Actualités:")
        print(f"   - Données complètes: {len(news_json)} caractères")
        print(f"   - Limitation actuelle: 1000 caractères")
        print(f"   - Données perdues: {max(0, len(news_json) - 1000)} caractères")
        
        # 5. Construire le contexte actuel (avec limitations)
        context_limited = f"""Données de marché actuelles (API Manus) pour {current_date}:

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

        # 6. Construire le contexte complet (sans limitations)
        context_complete = f"""Données de marché actuelles (API Manus) pour {current_date}:

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

        # 7. Comparer les tailles
        print("\n" + "="*80)
        print("📏 COMPARAISON DES TAILLES DE CONTEXTE")
        print("="*80)
        
        print(f"Contexte avec limitations: {len(context_limited)} caractères")
        print(f"Contexte complet: {len(context_complete)} caractères")
        print(f"Données perdues: {len(context_complete) - len(context_limited)} caractères")
        print(f"Pourcentage perdu: {((len(context_complete) - len(context_limited)) / len(context_complete) * 100):.1f}%")
        
        # 8. Vérifier les limites de tokens OpenAI
        print("\n" + "="*80)
        print("🤖 LIMITES OPENAI GPT-4o")
        print("="*80)
        
        # Estimation: 1 token ≈ 4 caractères
        tokens_limited = len(context_limited) // 4
        tokens_complete = len(context_complete) // 4
        
        print(f"Tokens estimés (contexte limité): {tokens_limited}")
        print(f"Tokens estimés (contexte complet): {tokens_complete}")
        print(f"Limite GPT-4o: 128,000 tokens")
        print(f"Marge disponible: {128000 - tokens_complete}")
        
        # 9. Recommandations
        print("\n" + "="*80)
        print("💡 RECOMMANDATIONS")
        print("="*80)
        
        if tokens_complete < 100000:  # Marge de sécurité
            print("✅ SUPPRIMER LES LIMITATIONS")
            print("   - Les données complètes peuvent être transmises")
            print("   - Plus d'informations pour ChatGPT")
            print("   - Analyse plus complète et précise")
        else:
            print("⚠️ OPTIMISER LES DONNÉES")
            print("   - Filtrer les données les plus importantes")
            print("   - Structurer les données de manière plus concise")
            print("   - Prioriser les informations clés")
        
        # 10. Sauvegarder les résultats
        with open(f"test_transmission_manus_{current_date}.txt", "w", encoding="utf-8") as f:
            f.write("=== TEST TRANSMISSION DONNÉES MANUS ===\n\n")
            f.write(f"Date: {current_date}\n\n")
            f.write("=== DONNÉES BRUTES ===\n")
            f.write(f"Marchés: {len(markets)} indices\n")
            f.write(f"Obligations: {len(bonds)} obligations\n")
            f.write(f"Cryptos: {len(cryptos)} cryptos\n")
            f.write(f"Commodités: {len(commodities)} commodités\n")
            f.write(f"Devises: {len(currencies)} paires\n")
            f.write(f"Indicateurs: {len(indicators)} indicateurs\n")
            f.write(f"Actualités: {len(news)} articles\n\n")
            f.write("=== LIMITATIONS ===\n")
            f.write(f"Contexte limité: {len(context_limited)} caractères\n")
            f.write(f"Contexte complet: {len(context_complete)} caractères\n")
            f.write(f"Données perdues: {len(context_complete) - len(context_limited)} caractères\n")
            f.write(f"Tokens estimés (complet): {tokens_complete}\n")
        
        print(f"\n💾 Résultats sauvegardés dans test_transmission_manus_{current_date}.txt")
        print("\n✅ Test terminé !")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_manus_data_transmission() 