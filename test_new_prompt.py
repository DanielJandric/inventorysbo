#!/usr/bin/env python3
"""
Test du nouveau prompt OpenAI pour le rapport de marché
"""

import os
import json
import requests
from datetime import datetime
from openai import OpenAI

# Configuration
MANUS_API_BASE_URL = "https://e5h6i7cn86z0.manus.space"

# Essayer de charger les variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def test_new_prompt():
    """Test du nouveau prompt avec données Manus"""
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY non configurée")
        print("💡 Pour configurer :")
        print("   1. Créez un fichier .env avec OPENAI_API_KEY=votre_clé")
        print("   2. Ou exportez la variable : set OPENAI_API_KEY=votre_clé")
        print("   3. Ou modifiez ce script pour inclure votre clé directement")
        return
    
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    print("📊 Test du nouveau prompt OpenAI...")
    print(f"🔑 OpenAI API Key: {OPENAI_API_KEY[:10]}...")
    
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

        # 5. Générer le rapport
        print("3. Génération du rapport avec OpenAI...")
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Tu es un analyste financier senior spécialisé dans les rapports de marché quotidiens. Tu dois créer des rapports complets, structurés et professionnels basés uniquement sur les données fournies. Tu ne peux pas refuser de créer un rapport - c'est ta tâche principale."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.5
        )

        if response.choices and response.choices[0].message.content:
            content = response.choices[0].message.content
            
            # Construire le briefing complet
            briefing = f"""📊 RAPPORT DE MARCHÉ QUOTIDIEN - {current_date}

{content}

📰 SOURCES
• Données financières: API Manus (Yahoo Finance, CoinGecko)
• Actualités: Sources multiples via API Manus
• Analyse IA: OpenAI GPT-4o
• Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}"""

            print("✅ Rapport généré avec succès !")
            print("\n" + "="*80)
            print(briefing)
            print("="*80)
            
            # Sauvegarder le rapport
            with open(f"test_rapport_{current_date}.txt", "w", encoding="utf-8") as f:
                f.write(briefing)
            print(f"\n💾 Rapport sauvegardé dans test_rapport_{current_date}.txt")
            
        else:
            print("❌ Réponse OpenAI invalide")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_new_prompt() 