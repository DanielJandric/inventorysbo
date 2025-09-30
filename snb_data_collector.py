"""
Script de collecte de données SNB
À exécuter manuellement ou via cron job

Usage:
    python snb_data_collector.py --collect-all
    python snb_data_collector.py --collect-cpi
    python snb_data_collector.py --collect-kof
"""

import os
import sys
import requests
from datetime import datetime, date
from typing import Dict, Any, Optional
import argparse

# Configuration
API_BASE_URL = os.getenv("SNB_API_BASE_URL", "https://inventorysbo.onrender.com")

def collect_cpi_manual() -> Dict[str, Any]:
    """
    Collecte manuelle du CPI
    
    Instructions :
    1. Allez sur https://www.bfs.admin.ch/bfs/fr/home/statistiques/prix/indice-prix-consommation.html
    2. Notez la valeur YoY (sur un an)
    3. Entrez les valeurs ci-dessous
    """
    print("\n=== COLLECTE CPI (OFS) ===")
    print("Source: https://www.bfs.admin.ch/bfs/fr/home/statistiques/prix/indice-prix-consommation.html")
    
    yoy_input = input("Inflation YoY (%) [ex: 0.2] : ")
    month_input = input("Mois (YYYY-MM) [ex: 2025-09] : ")
    
    try:
        yoy_pct = float(yoy_input)
        as_of = f"{month_input}-28"  # Approximation fin de mois
        
        return {
            "provider": "BFS",
            "as_of": as_of,
            "yoy_pct": yoy_pct,
            "mm_pct": None,
            "source_url": "https://www.bfs.admin.ch",
            "idempotency_key": f"bfs-{month_input}"
        }
    except ValueError:
        print("❌ Erreur: valeur invalide")
        sys.exit(1)


def collect_kof_manual() -> Dict[str, Any]:
    """
    Collecte manuelle du KOF
    
    Instructions :
    1. Allez sur https://kof.ethz.ch/en/forecasts-and-indicators/indicators/kof-economic-barometer.html
    2. Notez la valeur du baromètre
    3. Entrez les valeurs ci-dessous
    """
    print("\n=== COLLECTE KOF (ETH Zurich) ===")
    print("Source: https://kof.ethz.ch/en/forecasts-and-indicators/indicators/kof-economic-barometer.html")
    
    barometer_input = input("Baromètre KOF [ex: 97.4] : ")
    month_input = input("Mois (YYYY-MM) [ex: 2025-09] : ")
    
    try:
        barometer = float(barometer_input)
        as_of = f"{month_input}-30"  # Fin de mois
        
        return {
            "provider": "KOF",
            "as_of": as_of,
            "barometer": barometer,
            "source_url": "https://kof.ethz.ch",
            "idempotency_key": f"kof-{month_input}"
        }
    except ValueError:
        print("❌ Erreur: valeur invalide")
        sys.exit(1)


def collect_snb_forecast_manual() -> Dict[str, Any]:
    """
    Collecte manuelle des prévisions BNS
    
    Instructions :
    1. Allez sur https://www.snb.ch/fr/the-snb/mandates-goals/monetary-policy/monetary-policy-assessment
    2. Téléchargez le dernier PDF MPA
    3. Notez les prévisions d'inflation pour les 3 prochaines années
    """
    print("\n=== COLLECTE PRÉVISIONS BNS ===")
    print("Source: https://www.snb.ch/fr/the-snb/mandates-goals/monetary-policy/monetary-policy-assessment")
    
    meeting_date_input = input("Date de la réunion MPA (YYYY-MM-DD) [ex: 2025-12-12] : ")
    year1 = input("Année 1 (ex: 2025) : ")
    forecast1 = input(f"Prévision inflation {year1} (%) [ex: 0.2] : ")
    year2 = input("Année 2 (ex: 2026) : ")
    forecast2 = input(f"Prévision inflation {year2} (%) [ex: 0.5] : ")
    year3 = input("Année 3 (ex: 2027) : ")
    forecast3 = input(f"Prévision inflation {year3} (%) [ex: 0.7] : ")
    
    try:
        forecast = {
            year1: float(forecast1),
            year2: float(forecast2),
            year3: float(forecast3)
        }
        
        return {
            "meeting_date": meeting_date_input,
            "forecast": forecast,
            "source_url": "https://www.snb.ch",
            "pdf_url": f"https://www.snb.ch/en/publications/communication/monetary-policy-assessments/{meeting_date_input}.pdf",
            "idempotency_key": f"snb-mpa-{meeting_date_input}"
        }
    except ValueError:
        print("❌ Erreur: valeur invalide")
        sys.exit(1)


def collect_ois_manual() -> Dict[str, Any]:
    """
    Collecte manuelle de la courbe OIS
    
    Instructions :
    1. Allez sur https://www.eurex.com/ex-en/markets/int/mon/swiss-franc-derivatives
    2. Notez les taux pour différents tenors (3M, 6M, 12M, 24M)
    """
    print("\n=== COLLECTE COURBE OIS (Eurex) ===")
    print("Source: https://www.eurex.com/ex-en/markets/int/mon/swiss-franc-derivatives")
    
    as_of_input = input("Date (YYYY-MM-DD) [ex: 2025-09-30] : ")
    
    points = []
    for tenor in [3, 6, 9, 12, 18, 24]:
        rate_input = input(f"Taux {tenor}M (%) [ex: 0.10] : ")
        try:
            points.append({
                "tenor_months": tenor,
                "rate_pct": float(rate_input)
            })
        except ValueError:
            print(f"❌ Erreur pour {tenor}M, utilisation de 0.0")
            points.append({"tenor_months": tenor, "rate_pct": 0.0})
    
    return {
        "as_of": as_of_input,
        "points": points,
        "source_url": "https://www.eurex.com",
        "idempotency_key": f"ois-{as_of_input}"
    }


def ingest_data(endpoint: str, data: Dict[str, Any]) -> bool:
    """Envoie les données vers l'API"""
    try:
        url = f"{API_BASE_URL}/api/snb/ingest/{endpoint}"
        print(f"\n📤 Envoi vers {url}")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code in [200, 201]:
            print("✅ Données ingérées avec succès")
            return True
        elif response.status_code == 409:
            print("⚠️  Données déjà existantes (idempotency key)")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur d'envoi: {e}")
        return False


def run_model() -> bool:
    """Lance le calcul du modèle"""
    try:
        url = f"{API_BASE_URL}/api/snb/model/run"
        print(f"\n🧮 Calcul du modèle...")
        
        response = requests.post(url, json={}, timeout=60)
        
        if response.status_code == 200:
            print("✅ Modèle calculé avec succès")
            result = response.json()
            if result.get("success"):
                output = result.get("result", {})
                print(f"   → i* = {output.get('i_star_next_pct', 'N/A'):.2f}%")
                probs = output.get('probs', {})
                print(f"   → Probs: cut={probs.get('cut', 0):.1%}, hold={probs.get('hold', 0):.1%}, hike={probs.get('hike', 0):.1%}")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de calcul: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Collecteur de données SNB")
    parser.add_argument("--collect-all", action="store_true", help="Collecter toutes les données")
    parser.add_argument("--collect-cpi", action="store_true", help="Collecter CPI")
    parser.add_argument("--collect-kof", action="store_true", help="Collecter KOF")
    parser.add_argument("--collect-snb", action="store_true", help="Collecter prévisions BNS")
    parser.add_argument("--collect-ois", action="store_true", help="Collecter courbe OIS")
    parser.add_argument("--run-model", action="store_true", help="Lancer le calcul du modèle")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("🚀 Collecteur de données SNB")
    print(f"📍 API: {API_BASE_URL}")
    print("=" * 60)
    
    success = True
    
    if args.collect_all or args.collect_cpi:
        data = collect_cpi_manual()
        success &= ingest_data("cpi", data)
    
    if args.collect_all or args.collect_kof:
        data = collect_kof_manual()
        success &= ingest_data("kof", data)
    
    if args.collect_all or args.collect_snb:
        data = collect_snb_forecast_manual()
        success &= ingest_data("snb-forecast", data)
    
    if args.collect_all or args.collect_ois:
        data = collect_ois_manual()
        success &= ingest_data("ois", data)
    
    if args.run_model or args.collect_all:
        success &= run_model()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Collection terminée avec succès")
        print(f"🌐 Voir les résultats: {API_BASE_URL}/snb-taux")
    else:
        print("⚠️  Collection terminée avec des erreurs")
        sys.exit(1)


if __name__ == "__main__":
    main()

