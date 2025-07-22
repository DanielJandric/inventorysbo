#!/usr/bin/env python3
"""
Script pour vérifier et configurer les clés API sur Render
"""

import os
import requests
import json
from datetime import datetime

def check_api_keys():
    """Vérifie les clés API configurées"""
    print("🔍 Vérification des clés API...")
    print("=" * 50)
    
    # Vérifier les variables d'environnement
    alpha_key = os.environ.get('ALPHA_VANTAGE_KEY')
    eodhd_key = os.environ.get('EODHD_KEY')
    finnhub_key = os.environ.get('FINNHUB_KEY')
    
    print(f"ALPHA_VANTAGE_KEY: {'✅ Configurée' if alpha_key else '❌ Manquante'}")
    print(f"EODHD_KEY: {'✅ Configurée' if eodhd_key else '❌ Manquante'}")
    print(f"FINNHUB_KEY: {'✅ Configurée' if finnhub_key else '❌ Manquante'}")
    
    if alpha_key:
        print(f"   Alpha Vantage: {alpha_key[:8]}...{alpha_key[-4:]}")
    if eodhd_key:
        print(f"   EODHD: {eodhd_key[:8]}...{eodhd_key[-4:]}")
    if finnhub_key:
        print(f"   Finnhub: {finnhub_key[:8]}...{finnhub_key[-4:]}")
    
    print("\n🧪 Test des APIs...")
    print("=" * 50)
    
    # Test Alpha Vantage
    if alpha_key:
        print("🔍 Test Alpha Vantage...")
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={alpha_key}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data and data['Global Quote']:
                    print("   ✅ Alpha Vantage: Fonctionnel")
                else:
                    print("   ⚠️ Alpha Vantage: Pas de données (limite atteinte?)")
            else:
                print(f"   ❌ Alpha Vantage: Erreur {response.status_code}")
        except Exception as e:
            print(f"   ❌ Alpha Vantage: Erreur - {e}")
    else:
        print("   ❌ Alpha Vantage: Clé manquante")
    
    # Test EODHD
    if eodhd_key:
        print("🔍 Test EODHD...")
        try:
            url = f"https://eodhd.com/api/real-time/AAPL?fmt=json&api_token={eodhd_key}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and 'close' in data:
                    print("   ✅ EODHD: Fonctionnel")
                else:
                    print("   ⚠️ EODHD: Pas de données")
            else:
                print(f"   ❌ EODHD: Erreur {response.status_code}")
        except Exception as e:
            print(f"   ❌ EODHD: Erreur - {e}")
    else:
        print("   ❌ EODHD: Clé manquante")
    
    # Test Finnhub
    if finnhub_key:
        print("🔍 Test Finnhub...")
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={finnhub_key}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and 'c' in data:
                    print("   ✅ Finnhub: Fonctionnel")
                else:
                    print("   ⚠️ Finnhub: Pas de données")
            else:
                print(f"   ❌ Finnhub: Erreur {response.status_code}")
        except Exception as e:
            print(f"   ❌ Finnhub: Erreur - {e}")
    else:
        print("   ❌ Finnhub: Clé manquante")

def generate_render_config():
    """Génère la configuration pour Render"""
    print("\n📋 Configuration Render...")
    print("=" * 50)
    
    config = {
        "ALPHA_VANTAGE_KEY": "XCRQGI1OMS5381DE",
        "EODHD_KEY": "687ae6e8493e52.65071366",
        "FINNHUB_KEY": "d1tbknpr01qr2iithm20d1tbknpr01qr2iithm2g"
    }
    
    print("Variables d'environnement à configurer sur Render:")
    print("-" * 40)
    for key, value in config.items():
        print(f"{key}={value}")
    
    print("\n📝 Instructions:")
    print("1. Aller sur https://dashboard.render.com")
    print("2. Sélectionner votre service 'inventorysbo'")
    print("3. Aller dans 'Environment'")
    print("4. Ajouter ces variables d'environnement")
    print("5. Redéployer le service")

if __name__ == "__main__":
    check_api_keys()
    generate_render_config() 