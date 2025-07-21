#!/usr/bin/env python3
"""
Test simple du scraper Reuters
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reuters_scraper import ReutersScraper

def main():
    print("🧪 Test du scraper Reuters")
    print("=" * 50)
    
    scraper = ReutersScraper()
    
    # Test 1: Connexion
    print("1️⃣ Test de connexion...")
    try:
        response = scraper.session.get("https://www.reuters.com", timeout=5)
        print(f"✅ Connexion réussie: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return
    
    # Test 2: Actualités
    print("\n2️⃣ Test des actualités...")
    news = scraper.get_financial_news(max_news=2)
    
    if news:
        print(f"✅ {len(news)} actualités récupérées:")
        for i, article in enumerate(news, 1):
            print(f"   {i}. {article['title'][:80]}...")
    else:
        print("❌ Aucune actualité récupérée")
    
    # Test 3: Données de marché
    print("\n3️⃣ Test des données de marché...")
    market_data = scraper.get_market_data()
    
    if market_data:
        print(f"✅ {len(market_data)} données de marché récupérées")
        for name, value in list(market_data.items())[:3]:
            print(f"   {name}: {value}")
    else:
        print("❌ Aucune donnée de marché récupérée")
    
    print("\n🎯 Test terminé!")

if __name__ == "__main__":
    main() 