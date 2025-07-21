#!/usr/bin/env python3
"""
Test d'affichage du nouveau prompt OpenAI pour le rapport de marché
"""

import json
import requests
from datetime import datetime

# Configuration
MANUS_API_BASE_URL = "https://e5h6i7cn86z0.manus.space"

def test_prompt_display():
    """Test d'affichage du nouveau prompt avec données Manus"""
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    print("📊 Test d'affichage du nouveau prompt OpenAI...")
    
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
        
        # 3. Construire le contexte
        context = f"""Données de marché actuelles (API Manus) pour {current_date}:

MARCHÉS FINANCIERS:
{json.dumps(financial_data.get('financial_data', {}).get('markets', {}), indent=2, ensure_ascii=False)[:1000]}

OBLIGATIONS:
{json.dumps(financial_data.get('financial_data', {}).get('bonds', []), indent=2, ensure_ascii=False)[:500]}

CRYPTOMONNAIES:
{json.dumps(financial_data.get('crypto_data', {}).get('cryptocurrencies', []), indent=2, ensure_ascii=False)[:500]}

COMMODITÉS:
{json.dumps(financial_data.get('financial_data', {}).get('commodities', []), indent=2, ensure_ascii=False)[:500]}

DEVISES:
{json.dumps(financial_data.get('financial_data', {}).get('currencies', []), indent=2, ensure_ascii=False)[:500]}

INDICATEURS ÉCONOMIQUES:
{json.dumps(economic_data.get('economic_data', {}).get('indicators', {}), indent=2, ensure_ascii=False)[:1000]}

ACTUALITÉS:
{json.dumps(news_data.get('news_data', {}), indent=2, ensure_ascii=False)[:1000]}"""

        # 4. Nouveau prompt
        prompt = f"""Tu es un analyste financier senior. Tu dois créer un rapport de marché complet et professionnel pour {current_date} en utilisant EXCLUSIVEMENT les données fournies par l'API Manus.

INSTRUCTIONS OBLIGATOIRES :
1. CRÉE un rapport complet et structuré
2. UTILISE toutes les données disponibles
3. ANALYSE chaque classe d'actifs mentionnée
4. FOURNIS des insights concrets et actionnables
5. STRUCTURE ton rapport de manière professionnelle

STRUCTURE DU RAPPORT :
1. RÉSUMÉ EXÉCUTIF (2-3 phrases clés)
2. MARCHÉS ACTIONS (USA, Europe, Suisse, Asie si pertinent)
3. OBLIGATIONS ET TAUX (souverains, corporate, spreads)
4. CRYPTOMONNAIES (BTC, ETH, altcoins, régulation)
5. COMMODITÉS (pétrole, or, métaux, agriculture)
6. DEVISES (paires majeures, émergentes)
7. INDICATEURS ÉCONOMIQUES (inflation, emploi, PMI)
8. ACTUALITÉS IMPACTANTES (géopolitique, banques centrales)
9. PERSPECTIVES ET RISQUES (signaux à surveiller)

STYLE :
- Ton professionnel et direct
- Données chiffrées précises
- Analyse factuelle basée sur les données
- Insights stratégiques pour l'investisseur
- Longueur : 800-1200 mots

Données à analyser :
{context}

IMPORTANT : Si certaines données sont manquantes ou vides, indique-le clairement. Ne fais pas d'hypothèses sur des données non fournies. Base ton analyse UNIQUEMENT sur les données réelles disponibles."""

        # 5. Afficher le prompt et les données
        print("\n" + "="*80)
        print("🔍 NOUVEAU PROMPT OPENAI")
        print("="*80)
        print(prompt)
        print("="*80)
        
        # 6. Afficher les données disponibles
        print("\n" + "="*80)
        print("📊 DONNÉES DISPONIBLES")
        print("="*80)
        
        print(f"📈 Marchés financiers: {len(financial_data.get('financial_data', {}).get('markets', {}))} indices")
        print(f"📊 Obligations: {len(financial_data.get('financial_data', {}).get('bonds', []))} obligations")
        print(f"🪙 Cryptomonnaies: {len(financial_data.get('crypto_data', {}).get('cryptocurrencies', []))} cryptos")
        print(f"🛢️ Commodités: {len(financial_data.get('financial_data', {}).get('commodities', []))} commodités")
        print(f"💱 Devises: {len(financial_data.get('financial_data', {}).get('currencies', []))} paires")
        print(f"📊 Indicateurs économiques: {len(economic_data.get('economic_data', {}).get('indicators', {}))} indicateurs")
        print(f"📰 Actualités: {len(news_data.get('news_data', {}))} articles")
        
        # 7. Sauvegarder le prompt pour référence
        with open(f"nouveau_prompt_{current_date}.txt", "w", encoding="utf-8") as f:
            f.write("=== NOUVEAU PROMPT OPENAI ===\n\n")
            f.write(prompt)
            f.write("\n\n=== DONNÉES DISPONIBLES ===\n\n")
            f.write(f"Marchés: {len(financial_data.get('financial_data', {}).get('markets', {}))}\n")
            f.write(f"Obligations: {len(financial_data.get('financial_data', {}).get('bonds', []))}\n")
            f.write(f"Cryptos: {len(financial_data.get('crypto_data', {}).get('cryptocurrencies', []))}\n")
            f.write(f"Commodités: {len(financial_data.get('financial_data', {}).get('commodities', []))}\n")
            f.write(f"Devises: {len(financial_data.get('financial_data', {}).get('currencies', []))}\n")
            f.write(f"Indicateurs: {len(economic_data.get('economic_data', {}).get('indicators', {}))}\n")
            f.write(f"Actualités: {len(news_data.get('news_data', {}))}\n")
        
        print(f"\n💾 Prompt sauvegardé dans nouveau_prompt_{current_date}.txt")
        print("\n✅ Test terminé - Le nouveau prompt est prêt à être utilisé !")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_prompt_display() 