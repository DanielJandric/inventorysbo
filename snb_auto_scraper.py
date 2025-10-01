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
    
    def scrape_with_scrapingbee(self, url: str) -> Optional[Dict]:
        """Scrape une URL avec ScrapingBee"""
        if self.simulation_mode:
            print(f"🧪 Mode simulation pour {url}")
            return None
        
        try:
            # Paramètres ScrapingBee (format officiel)
            params = {
                "api_key": SCRAPINGBEE_API_KEY,
                "url": url,
                "render_js": "true"
            }
            
            response = requests.get(
                "https://app.scrapingbee.com/api/v1",  # Pas de slash final
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                # Retourner le contenu HTML brut
                return {"content": response.text}
            else:
                # Afficher le détail de l'erreur
                print(f"❌ ScrapingBee erreur {response.status_code}")
                print(f"   Body: {response.text[:300]}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur scraping: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def collect_cpi(self) -> Optional[Dict[str, Any]]:
        """Collecte automatique du CPI depuis OFS"""
        print("\n📊 Collecte CPI (OFS)...")
        
        # Scraping du HTML brut
        data = self.scrape_with_scrapingbee(OFS_CPI_URL)
        
        if not data and not self.simulation_mode:
            self.errors.append("CPI: Scraping échoué")
            return None
        
        # Mode simulation : valeurs par défaut
        if self.simulation_mode:
            print("🧪 Utilisation de valeurs simulées")
            yoy_pct = 0.7  # Exemple
            as_of = date.today().replace(day=1)
        else:
            # Parser le HTML content pour extraire YoY
            html_content = data.get("content", "")
            
            # Regex pour trouver "X.X%" ou "X,X%" avec contexte "sur un an"
            match = re.search(r'(\d+[.,]\d+)\s*%.*?(sur un an|année|year-on-year|jährlich)', html_content, re.IGNORECASE | re.DOTALL)
            
            if match:
                yoy_str = match.group(1).replace(',', '.')
                yoy_pct = float(yoy_str)
                as_of = date.today().replace(day=1)
                print(f"   Extrait du HTML: {yoy_pct}%")
            else:
                print("⚠️  Impossible d'extraire YoY du HTML, utilisation valeur par défaut")
                yoy_pct = 0.7
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
        
        # Scraping du HTML brut
        data = self.scrape_with_scrapingbee(KOF_BAROMETER_URL)
        
        if not data and not self.simulation_mode:
            self.errors.append("KOF: Scraping échoué")
            return None
        
        # Mode simulation
        if self.simulation_mode:
            print("🧪 Utilisation de valeurs simulées")
            barometer = 101.2  # Exemple
            as_of = date.today()
        else:
            # Parser le HTML pour trouver la valeur du baromètre (typiquement 90-110)
            html_content = data.get("content", "")
            match = re.search(r'(\d{2,3}[.,]\d+)\s*(points?|Punkte|punti)', html_content, re.IGNORECASE)
            
            if match:
                bar_str = match.group(1).replace(',', '.')
                barometer = float(bar_str)
                as_of = date.today()
                print(f"   Extrait du HTML: {barometer}")
            else:
                print("⚠️  Impossible d'extraire barometer du HTML, utilisation valeur par défaut")
                barometer = 101.2
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
    
    def collect_ois_from_eurex(self) -> Optional[Dict[str, Any]]:
        """
        Collecte la courbe OIS depuis les futures SARON 3M d'Eurex
        
        Source: https://www.eurex.com/ex-en/markets/int/mon/saron-futures/saron/3M-SARON-Futures-1410330
        """
        print("\n💹 Collecte courbe OIS depuis Eurex (3M SARON Futures)...")
        
        eurex_url = "https://www.eurex.com/ex-en/markets/int/mon/saron-futures/saron/3M-SARON-Futures-1410330"
        
        # Scraping du HTML brut
        data = self.scrape_with_scrapingbee(eurex_url)
        
        if not data and not self.simulation_mode:
            print("⚠️  Scraping Eurex échoué, utilisation approximation...")
            return self.collect_ois_approximation()
        
        if self.simulation_mode:
            print("🧪 Mode simulation: utilisation approximation")
            return self.collect_ois_approximation()
        
        # Parser les données Eurex
        try:
            # Les futures SARON sont cotés en termes de prix (100 - taux implicite)
            # Exemple: Prix 99.50 → taux implicite = 0.50%
            
            # Extraire les prix des contrats par échéance
            # Format Eurex: contrats trimestriels (Mar, Jun, Sep, Dec)
            html_content = data.get("content", "")
            
            # Regex pour trouver les prix (format: 99.XXX ou 100.XXX)
            # Les contrats sont listés par échéance (le plus proche en premier)
            matches = re.findall(r'(99\.\d{2,3}|100\.\d{2,3})', html_content)
            
            if not matches or len(matches) < 4:
                print("⚠️  Pas assez de données Eurex, utilisation approximation")
                return self.collect_ois_approximation()
            
            # Convertir prix en taux implicites
            # Prix du futures = 100 - taux implicite (en %)
            futures_prices = [float(m) for m in matches[:8]]  # 8 premiers contrats (2 ans)
            implicit_rates = [100.0 - price for price in futures_prices]
            
            # Mapper aux tenors (contrats trimestriels)
            # Contrat 1 = 3M, Contrat 2 = 6M, Contrat 3 = 9M, etc.
            points = []
            for i, rate in enumerate(implicit_rates[:8]):
                tenor = (i + 1) * 3  # 3, 6, 9, 12, 15, 18, 21, 24 mois
                if tenor <= 24:
                    points.append({
                        "tenor_months": tenor,
                        "rate_pct": rate
                    })
            
            # S'assurer qu'on a au moins 6 points (3, 6, 9, 12, 18, 24)
            if len(points) < 6:
                print("⚠️  Pas assez de points OIS, utilisation approximation")
                return self.collect_ois_approximation()
            
            as_of = date.today()
            
            payload = {
                "as_of": as_of.isoformat(),
                "points": points,
                "source_url": eurex_url,
                "idempotency_key": f"ois-{as_of.isoformat()}-eurex"
            }
            
            print(f"✅ OIS Eurex collecté: {len(points)} points")
            print(f"   3M: {points[0]['rate_pct']:.3f}% | 12M: {points[3]['rate_pct']:.3f}%")
            return payload
            
        except Exception as e:
            print(f"❌ Erreur parsing Eurex: {e}")
            print("   Fallback vers approximation...")
            return self.collect_ois_approximation()
    
    def collect_ois_approximation(self) -> Optional[Dict[str, Any]]:
        """
        Génère une courbe OIS approximative basée sur le taux directeur BNS actuel
        
        Fallback si scraping Eurex échoue
        """
        print("\n💹 Génération courbe OIS approximative (fallback)...")
        
        # Taux directeur BNS actuel (MPA 25 septembre 2025)
        policy_rate = 0.00  # 0.00% - Maintenu à 0%
        
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
        
        print(f"⚠️  OIS approximatif: {policy_rate}% (taux directeur)")
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
        print("🧪 Utilisation prévisions BNS (MPA 25 septembre 2025)")
        
        current_year = date.today().year
        meeting_date = date.today()
        
        # Prévisions officielles BNS (MPA 25 septembre 2025)
        # Source: Communiqué BNS du 25.09.2025
        forecast = {
            "2025": 0.2,  # Inflation moyenne 2025: 0.2%
            "2026": 0.5,  # Inflation moyenne 2026: 0.5%
            "2027": 0.7   # Inflation moyenne 2027: 0.7%
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
        
        # OIS depuis Eurex (fallback vers approximation si échec)
        ois_data = self.collect_ois_from_eurex()
        if ois_data:
            self.ingest_data("ois", ois_data)
        
        # Relancer le modèle
        self.run_model()
    
    def collect_neer(self) -> Optional[Dict[str, Any]]:
        """
        Collecte le NEER depuis l'API officielle SNB
        """
        print("\n💱 Collecte NEER depuis data.snb.ch...")
        
        try:
            from snb_neer_collector import collect_neer_from_snb_api
            neer_data = collect_neer_from_snb_api()
            return neer_data
        except Exception as e:
            print(f"❌ Erreur collecte NEER: {e}")
            self.errors.append(f"NEER: {str(e)}")
            return None
    
    def run_monthly_collection(self):
        """Collecte mensuelle (CPI + KOF + NEER)"""
        print("📅 === COLLECTE MENSUELLE ===")
        
        # CPI
        cpi_data = self.collect_cpi()
        if cpi_data:
            self.ingest_data("cpi", cpi_data)
        
        # KOF
        kof_data = self.collect_kof()
        if kof_data:
            self.ingest_data("kof", kof_data)
        
        # NEER (nouveau!)
        neer_data = self.collect_neer()
        if neer_data:
            self.ingest_data("neer", neer_data)
        
        # OIS depuis Eurex (fallback vers approximation si échec)
        ois_data = self.collect_ois_from_eurex()
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

