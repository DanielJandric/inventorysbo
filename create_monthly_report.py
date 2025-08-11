#!/usr/bin/env python3
"""
Création d'un rapport mensuel (Août 2025) dans Supabase et envoi par email via le worker.

À exécuter sur Render (où les variables d'environnement SUPABASE_* et EMAIL_* sont configurées):

    python create_monthly_report.py

"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, List

from market_analysis_db import MarketAnalysis, get_market_analysis_db
from background_worker import MarketAnalysisWorker


def build_monthly_report_payload() -> Dict:
    """Construit le payload du rapport mensuel Août 2025 (valeurs fournies par l'utilisateur)."""
    executive_summary: List[str] = [
        "• États‑Unis: CPI 2,7% (core 2,9%), Fed 4,25–4,50%, PIB T2 +3,0% (annualisé), chômage 4,2%, NFP +73k",
        "• Zone euro: HICP 2,0% (core 2,3%), T2: +0,1% QoQ / +1,4% YoY, BCE dépôt 2,00% / refi 2,15%",
        "• Suisse: CPI 0,2% (core 0,8%), BNS 0,00%, chômage 2,7% (2,9% SA), PIB T1 +0,5% QoQ",
        "• Chine: PIB T2 +5,2% YoY (+1,1% QoQ) → dynamique robuste malgré tensions",
        "• Divergence monétaire: Fed restrictive, BCE modérée, BNS à 0% → impacts FX et flux sectoriels"
    ]

    summary = (
        "Rapport mensuel – Août 2025\n\n"
        "États‑Unis: désinflation graduelle (CPI 2,7%, core 2,9%), croissance T2 solide (+3,0% annualisé) "
        "mais normalisation du marché du travail (chômage 4,2%, NFP +73k). Fed maintient une posture restrictive en "
        "attente de signaux plus nets sur prix/salaires.\n\n"
        "Zone euro: désinflation validée (HICP 2,0%, core 2,3%), activité quasi-stable (T2 +0,1% QoQ / +1,4% YoY). "
        "Contraintes structurelles limitent l'élan de croissance.\n\n"
        "Suisse: environnement quasi‑déflationniste (CPI 0,2%, core 0,8%) avec BNS à 0,00%. CHF valeur refuge "
        "continue de peser, mais l'économie reste résiliente (PIB T1 +0,5% QoQ).\n\n"
        "Chine: T2 solide (+5,2% YoY, +1,1% QoQ), soutenu par politiques ciblées; risques: immobilier, commerce, "
        "géopolitique.\n\n"
        "Thèmes: divergence monétaire (Fed/BCE/BNS), désinflation à vitesses différenciées, stabilisation cyclique en Chine."
    )

    key_points: List[str] = [
        "Divergence de politiques: USD soutenu vs EUR/CHF (tendance de fond)",
        "Désinflation globale mais hétérogène: duration/qualité favorisées en Europe/Suisse",
        "Stabilisation Chine: potentiels soutiens matières premières si l'élan perdure",
        "Risque US: ré‑accélération prix/salaires prolongerait la restriction"
    ]

    geopolitical_analysis = {
        "conflicts": [
            "Tensions commerciales récurrentes US–Chine: vigilance sur chaînes d'approvisionnement",
        ],
        "trade_relations": [
            "Europe: normalisation lente des flux, dépendance au cycle US/Asie",
        ],
        "sanctions": [
            "Veille continue: effets principalement visibles sur énergie et logistique",
        ],
        "energy_security": [
            "Prix énergie: surveillance WTI/Brent et stocks US pour biais inflation",
        ],
    }

    economic_indicators = {
        "inflation": {"US": "2.7%", "EU": "2.0%", "CH": "0.2%", "trend": "désinflation hétérogène"},
        "central_banks": ["Fed: 4.25–4.50%", "BCE: 2.00–2.15%", "BNS: 0.00%"],
        "gdp_growth": {"US": "+3.0% (T2 annualisé)", "Eurozone": "+0.1% QoQ / +1.4% YoY", "China": "+5.2% YoY"},
        "unemployment": {"US": "4.2%", "CH": "2.7% (2.9% SA)"}
    }

    sources = [
        {"title": "BEA – GDP", "url": "https://www.bea.gov/"},
        {"title": "BLS – Employment Situation", "url": "https://www.bls.gov/"},
        {"title": "Federal Reserve (FOMC)", "url": "https://www.federalreserve.gov/"},
        {"title": "Eurostat", "url": "https://ec.europa.eu/eurostat"},
        {"title": "ECB SDW", "url": "https://sdw.ecb.europa.eu/"},
        {"title": "BNS Data", "url": "https://data.snb.ch/"},
        {"title": "Trading Economics", "url": "https://tradingeconomics.com/"},
        {"title": "FRED API", "url": "https://fred.stlouisfed.org/docs/api/"},
    ]

    result = {
        "executive_summary": executive_summary,
        "summary": summary,
        "key_points": key_points,
        "geopolitical_analysis": geopolitical_analysis,
        "economic_indicators": economic_indicators,
        "insights": [],
        "risks": [
            "US: risque de ré‑accélération de l'inflation (énergie/salaires)",
            "EU: activité molle prolongée, bénéfices fragiles",
            "CH: force du CHF pèse sur marges exportatrices",
            "CN: aléas immobiliers et tensions commerciales"
        ],
        "opportunities": [
            "Qualité défensive US, leaders suisses globaux",
            "Valeur/rendement en Europe si inflation ancrée à 2%",
            "Exposition sélective matières premières si Chine confirme l'élan"
        ],
        "sources": sources,
        "confidence_score": 0.9,
    }

    return result


def main() -> None:
    db = get_market_analysis_db()
    if not db.is_connected():
        raise RuntimeError("Supabase non configuré (SUPABASE_URL/SUPABASE_KEY)")

    result = build_monthly_report_payload()

    analysis = MarketAnalysis(
        analysis_type='monthly',
        prompt='Rapport mensuel – Août 2025 (données fournies)',
        executive_summary=result.get('executive_summary'),
        summary=result.get('summary'),
        key_points=result.get('key_points'),
        structured_data={},
        geopolitical_analysis=result.get('geopolitical_analysis'),
        economic_indicators=result.get('economic_indicators'),
        insights=result.get('insights'),
        risks=result.get('risks'),
        opportunities=result.get('opportunities'),
        sources=result.get('sources'),
        confidence_score=result.get('confidence_score', 0.0),
        worker_status='completed',
        processing_time_seconds=0,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    analysis_id = db.save_analysis(analysis)
    if not analysis_id:
        raise RuntimeError("Échec d'insertion du rapport mensuel")

    print(f"✅ Rapport mensuel inséré avec l'ID {analysis_id}")

    # Envoi email via le worker (utilise le template HTML et récupère le snapshot marché)
    worker = MarketAnalysisWorker()
    asyncio.run(worker._send_market_analysis_email(analysis_id, result))
    print("📧 Email du rapport mensuel envoyé (si EMAIL_* configuré)")


if __name__ == "__main__":
    main()


