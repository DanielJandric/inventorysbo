#!/usr/bin/env python3
import json
from datetime import datetime

from app import gmail_manager


def main():
    sample = {
        "executive_summary": [
            "Risque modéré, VIX bas; USD en repli",
            "AI megacaps soutiennent les indices",
            "Pente 2s10s s'accentue, front-end en baisse",
        ],
        "summary": "Marchés en mode risk-on tactique, avec consolidation contrôlée et soutien des mégacaps IA.",
        "economic_indicators": {
            "inflation": {"US": "2.5% YoY", "EU": "2.2% YoY"},
            "central_banks": ["Fed 4.75%", "BCE 3.75%"],
        },
        "geopolitical_analysis": {
            "immediate_impacts": [
                {"event": "Tensions Moyen-Orient", "affected_assets": ["WTI", "Gold"], "magnitude": "+1-2%", "duration": "court"}
            ]
        },
        "key_points": ["USD-", "VIX<15", "Crude +1%"],
        "insights": ["Flows retail en hausse sur AI"],
        "risks": ["Choc inflation PCE"],
        "opportunities": ["Hedges convexes peu chers"],
        "sources": [
            {"title": "MarketWatch", "url": "https://www.marketwatch.com/"},
            {"title": "Bloomberg", "url": "https://www.bloomberg.com/"},
        ],
        "confidence_score": 0.62,
    }

    html = gmail_manager._create_market_report_html_v2(
        datetime.now().strftime("%d/%m/%Y"),
        datetime.now().strftime("%H:%M"),
        json.dumps(sample, ensure_ascii=False),
    )
    out = "_local_market_report_preview.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Aperçu généré: {out}")


if __name__ == "__main__":
    main()


