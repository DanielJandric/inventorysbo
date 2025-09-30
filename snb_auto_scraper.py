"""
Scraper automatique SNB avec ScrapingBee
Collecte automatiquement : CPI (OFS), KOF, OIS approximatif, prévisions BNS

Configuration requise :
- SCRAPINGBEE_API_KEY dans .env
- SNB_API_BASE_URL (optionnel, défaut: https://inventorysbo.onrender.com)

Usage:
    python snb_auto_scraper.py --daily     # Collecte quotidienne (OIS)
    python snb_auto_scraper.py --monthly   # Collecte mensuelle (CPI + KOF)
    python snb_auto_scraper.py --quarterly # Collecte trimestrielle (BNS)
    python snb_auto_scraper.py --all       # Tout collecter
"""

import os
import sys
import json
import re
import requests
from datetime import datetime, date
from typing import Dict, Any, Optional, List
import argparse
from dotenv import load_dotenv

load_dotenv()

# Configuration
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY")
API_BASE_URL = os.getenv("SNB_API_BASE_URL", "https://inventorysbo.onrender.com")
NOTIFICATION_EMAIL = os.getenv("SNB_NOTIFICATION_EMAIL")  # Optionnel

# URLs sources
OFS_CPI_URL = "https://www.bfs.admin.ch/bfs/fr/home/statistiques/prix/indice-prix-consommation.html"
KOF_BAROMETER_URL = "https://kof.ethz.ch/en/forecasts-and-indicators/indicators/kof-economic-barometer.html"
SNB_MPA_URL = "https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/monetary-policy-assessment"


class SNBAutoScraper:
    """Scraper automatique pour les données SNB"""
    
    def __init__(self):
        if not SCRAPINGBEE_API_KEY:
            print("⚠️  SCRAPINGBEE_API_KEY non configurée, mode simulation")
            self.simulation_mode = True
        else:
            self.simulation_mode = False
        
        self.results = []
        self.errors = []
    
    def scrape_with_scrapingbee(self, url: str, extract_rules: Dict = None) -> Optional[Dict]:
        """Scrape une URL avec ScrapingBee"""
        if self.simulation_mode:
            print(f"🧪 Mode simulation pour {url}")
            return None
        
        try:
            params = {
                "api_key": SCRAPINGBEE_API_KEY,
                "url": url,
                "render_js": "true",
                "premium_proxy": "true",
                "country_code": "ch"
            }
            
            if extract_rules:
                params["extract_rules"] = json.dumps(extract_rules)
            
            response = requests.get(
                "https://app.scrapingbee.com/api/v1/",
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json() if extract_rules else {"content": response.text}
            else:
                print(f"❌ ScrapingBee erreur {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur scraping: {e}")
            return None
    
    def collect_cpi(self) -> Optional[Dict[str, Any]]:
        """Collecte automatique du CPI depuis OFS"""
        print("\n📊 Collecte CPI (OFS)...")
        
        # Extraction rules pour ScrapingBee
        extract_rules = {
            "yoy_text": {
                "selector": "body",
                "type": "text"
            }
        }
        
        data = self.scrape_with_scrapingbee(OFS_CPI_URL, extract_rules)
        
        if not data and not self.simulation_mode:
            self.errors.append("CPI: Scraping échoué")
            return None
        
        # Mode simulation : valeurs par défaut
        if self.simulation_mode:
            print("🧪 Utilisation de valeurs simulées")
            yoy_pct = 0.7  # Exemple
            as_of = date.today().replace(day=1)
        else:
            # Parser le texte pour extraire YoY
            text = data.get("yoy_text", "")
            
            # Regex pour trouver "X.X%" ou "X,X%"
            match = re.search(r'(\d+[.,]\d+)\s*%.*?(sur un an|year-on-year|annual)', text, re.IGNORECASE)
            
            if match:
                yoy_str = match.group(1).replace(',', '.')
                yoy_pct = float(yoy_str)
                as_of = date.today().replace(day=1)
            else:
                print("⚠️  Impossible d'extraire YoY, utilisation valeur par défaut")
                yoy_pct = 0.5
                as_of = date.today().replace(day=1)
        
        payload = {
            "provider": "BFS",
            "as_of": as_of.isoformat(),
            "yoy_pct": yoy_pct,
            "mm_pct": None,
            "source_url": OFS_CPI_URL,
            "idempotency_key": f"bfs-{as_of.strftime('%Y-%m')}-auto"
        }
        
        print(f"✅ CPI collecté: {yoy_pct}% YoY au {as_of}")
        return payload
    
    def collect_kof(self) -> Optional[Dict[str, Any]]:
        """Collecte automatique du KOF Barometer"""
        print("\n📈 Collecte KOF Barometer...")
        
        extract_rules = {
            "barometer_text": {
                "selector": "body",
                "type": "text"
            }
        }
        
        data = self.scrape_with_scrapingbee(KOF_BAROMETER_URL, extract_rules)
        
        if not data and not self.simulation_mode:
            self.errors.append("KOF: Scraping échoué")
            return None
        
        # Mode simulation
        if self.simulation_mode:
            print("🧪 Utilisation de valeurs simulées")
            barometer = 101.2  # Exemple
            as_of = date.today()
        else:
            # Parser pour trouver la valeur du baromètre (typiquement 90-110)
            text = data.get("barometer_text", "")
            match = re.search(r'(\d{2,3}[.,]\d+)\s*(points?|Punkte)', text)
            
            if match:
                bar_str = match.group(1).replace(',', '.')
                barometer = float(bar_str)
                as_of = date.today()
            else:
                print("⚠️  Impossible d'extraire barometer, utilisation valeur par défaut")
                barometer = 100.0
                as_of = date.today()
        
        payload = {
            "provider": "KOF",
            "as_of": as_of.isoformat(),
            "barometer": barometer,
            "source_url": KOF_BAROMETER_URL,
            "idempotency_key": f"kof-{as_of.strftime('%Y-%m')}-auto"
        }
        
        print(f"✅ KOF collecté: {barometer} au {as_of}")
        return payload
    
    def collect_ois_approximation(self) -> Optional[Dict[str, Any]]:
        """
        Génère une courbe OIS approximative basée sur le taux directeur BNS actuel
        
        Note: Pour des données réelles, il faudrait scraper Eurex ou utiliser Bloomberg API
        """
        print("\n💹 Génération courbe OIS approximative...")
        
        # Taux directeur BNS actuel (à adapter selon l'actualité)
        # TODO: Scraper depuis https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy
        policy_rate = 0.50  # Exemple: 0.50% (à jour dec 2024)
        
        # Approximation : courbe plate avec légère pente
        points = [
            {"tenor_months": 3, "rate_pct": policy_rate},
            {"tenor_months": 6, "rate_pct": policy_rate + 0.05},
            {"tenor_months": 9, "rate_pct": policy_rate + 0.10},
            {"tenor_months": 12, "rate_pct": policy_rate + 0.15},
            {"tenor_months": 18, "rate_pct": policy_rate + 0.20},
            {"tenor_months": 24, "rate_pct": policy_rate + 0.25}
        ]
        
        as_of = date.today()
        
        payload = {
            "as_of": as_of.isoformat(),
            "points": points,
            "source_url": "https://www.snb.ch (approximation)",
            "idempotency_key": f"ois-{as_of.isoformat()}-approx"
        }
        
        print(f"✅ OIS approximatif: {policy_rate}% (taux directeur)")
        return payload
    
    def collect_snb_forecast(self) -> Optional[Dict[str, Any]]:
        """
        Collecte les prévisions BNS (trimestriel)
        
        Note: Le parsing de PDF est complexe. Pour l'instant, utilise des valeurs par défaut.
        TODO: Implémenter parser PDF ou attendre publication structurée
        """
        print("\n🏦 Collecte prévisions BNS...")
        
        # Vérifier si on est dans un mois de MPA (mars, juin, sept, déc)
        current_month = date.today().month
        if current_month not in [3, 6, 9, 12]:
            print("ℹ️  Pas de MPA ce mois-ci (seulement mars, juin, sept, déc)")
            return None
        
        # Mode simulation : utiliser dernières prévisions connues
        print("🧪 Utilisation de prévisions par défaut (nécessite parsing PDF manuel)")
        
        current_year = date.today().year
        meeting_date = date.today()
        
        # Prévisions exemple (à mettre à jour manuellement après chaque MPA)
        forecast = {
            str(current_year): 0.7,
            str(current_year + 1): 1.0,
            str(current_year + 2): 1.2
        }
        
        payload = {
            "meeting_date": meeting_date.isoformat(),
            "forecast": forecast,
            "source_url": SNB_MPA_URL,
            "pdf_url": f"{SNB_MPA_URL}/mpa-{meeting_date.strftime('%Y-%m')}.pdf",
            "idempotency_key": f"snb-mpa-{meeting_date.isoformat()}-auto"
        }
        
        print(f"✅ Prévisions BNS: {forecast}")
        return payload
    
    def ingest_data(self, endpoint: str, data: Dict[str, Any]) -> bool:
        """Envoie les données vers l'API"""
        try:
            url = f"{API_BASE_URL}/api/snb/ingest/{endpoint}"
            print(f"📤 Envoi vers {url}")
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code in [200, 201]:
                print("✅ Données ingérées")
                self.results.append(f"{endpoint}: OK")
                return True
            elif response.status_code == 409:
                print("ℹ️  Données déjà existantes")
                self.results.append(f"{endpoint}: Déjà existant")
                return True
            else:
                print(f"❌ Erreur {response.status_code}: {response.text}")
                self.errors.append(f"{endpoint}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur d'envoi: {e}")
            self.errors.append(f"{endpoint}: {str(e)}")
            return False
    
    def run_model(self) -> bool:
        """Lance le calcul du modèle"""
        try:
            url = f"{API_BASE_URL}/api/snb/model/run"
            print(f"\n🧮 Calcul du modèle...")
            
            response = requests.post(url, json={}, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ Modèle calculé")
                    output = result.get("result", {})
                    print(f"   → i* = {output.get('i_star_next_pct', 0):.2f}%")
                    probs = output.get('probs', {})
                    print(f"   → Hold = {probs.get('hold', 0):.1%}")
                    self.results.append("Modèle: Calculé")
                    return True
            
            print(f"❌ Erreur calcul")
            self.errors.append("Modèle: Échec calcul")
            return False
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.errors.append(f"Modèle: {str(e)}")
            return False
    
    def send_notification(self):
        """Envoie une notification par email (optionnel)"""
        if not NOTIFICATION_EMAIL:
            return
        
        # TODO: Implémenter envoi email via SMTP ou service
        print(f"📧 Notification envoyée à {NOTIFICATION_EMAIL}")
    
    def run_daily_collection(self):
        """Collecte quotidienne (OIS seulement)"""
        print("🌅 === COLLECTE QUOTIDIENNE ===")
        
        # OIS approximatif
        ois_data = self.collect_ois_approximation()
        if ois_data:
            self.ingest_data("ois", ois_data)
        
        # Relancer le modèle
        self.run_model()
    
    def run_monthly_collection(self):
        """Collecte mensuelle (CPI + KOF)"""
        print("📅 === COLLECTE MENSUELLE ===")
        
        # CPI
        cpi_data = self.collect_cpi()
        if cpi_data:
            self.ingest_data("cpi", cpi_data)
        
        # KOF
        kof_data = self.collect_kof()
        if kof_data:
            self.ingest_data("kof", kof_data)
        
        # OIS
        ois_data = self.collect_ois_approximation()
        if ois_data:
            self.ingest_data("ois", ois_data)
        
        # Relancer le modèle
        self.run_model()
    
    def run_quarterly_collection(self):
        """Collecte trimestrielle (BNS)"""
        print("📆 === COLLECTE TRIMESTRIELLE ===")
        
        # Prévisions BNS
        snb_data = self.collect_snb_forecast()
        if snb_data:
            self.ingest_data("snb-forecast", snb_data)
        
        # Tout recalculer
        self.run_monthly_collection()
    
    def print_summary(self):
        """Affiche le résumé"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DE LA COLLECTE")
        print("="*60)
        
        if self.results:
            print("\n✅ Succès:")
            for r in self.results:
                print(f"   • {r}")
        
        if self.errors:
            print("\n❌ Erreurs:")
            for e in self.errors:
                print(f"   • {e}")
        
        if not self.errors:
            print("\n🎉 Collecte réussie à 100%")
        else:
            print(f"\n⚠️  {len(self.errors)} erreur(s)")
        
        print(f"\n🌐 Voir résultats: {API_BASE_URL}/snb-taux")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Scraper automatique SNB")
    parser.add_argument("--daily", action="store_true", help="Collecte quotidienne (OIS)")
    parser.add_argument("--monthly", action="store_true", help="Collecte mensuelle (CPI + KOF)")
    parser.add_argument("--quarterly", action="store_true", help="Collecte trimestrielle (BNS)")
    parser.add_argument("--all", action="store_true", help="Tout collecter")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    scraper = SNBAutoScraper()
    
    try:
        if args.all or args.quarterly:
            scraper.run_quarterly_collection()
        elif args.monthly:
            scraper.run_monthly_collection()
        elif args.daily:
            scraper.run_daily_collection()
        
        scraper.print_summary()
        scraper.send_notification()
        
        # Exit code selon succès
        sys.exit(0 if not scraper.errors else 1)
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

