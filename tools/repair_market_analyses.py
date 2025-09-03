#!/usr/bin/env python3
"""
Répare les enregistrements existants de market_analyses:
- Convertit les champs JSON stringifiés en vrais JSON valides
- Remplace les JSON invalides par [] / {}
- Nettoie le champ summary si du JSON a été collé

Usage:
  python -m tools.repair_market_analyses
"""

import os
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('repair_market_analyses')


def _safe_json_load(val, default):
    if isinstance(val, (list, dict)):
        return val
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return default
        try:
            return json.loads(s)
        except Exception:
            return default
    return default


def _clean_summary(s: str) -> str:
    try:
        txt = str(s or '').strip()
        if not txt:
            return ''
        if txt.startswith('{') and ('"deep_analysis"' in txt or '"meta_analysis"' in txt):
            try:
                obj = json.loads(txt)
                if isinstance(obj, dict):
                    cand = obj.get('summary') or ((obj.get('deep_analysis') or {}).get('narrative') if isinstance(obj.get('deep_analysis'), dict) else '')
                    if cand:
                        return str(cand)
            except Exception:
                return txt
        return txt
    except Exception:
        return str(s or '')


def run():
    from market_analysis_db import get_market_analysis_db
    db = get_market_analysis_db()
    if not db.is_connected():
        logger.error('Pas de connexion à la base Supabase')
        return

    # Récupérer un lot large pour réparation
    analyses = db.get_recent_analyses(limit=200)
    fixed = 0
    for a in analyses:
        try:
            needs_update = False

            # Champs liste
            for fld in ['executive_summary', 'key_points', 'insights', 'risks', 'opportunities', 'sources']:
                val = getattr(a, fld, None)
                parsed = _safe_json_load(val, [])
                if parsed != val:
                    setattr(a, fld, parsed)
                    needs_update = True

            # Champs dict
            for fld in ['structured_data', 'geopolitical_analysis', 'economic_indicators']:
                val = getattr(a, fld, None)
                parsed = _safe_json_load(val, {})
                if parsed != val:
                    setattr(a, fld, parsed)
                    needs_update = True

            # Summary nettoyé si JSON collé
            new_summary = _clean_summary(getattr(a, 'summary', '') or '')
            if new_summary != getattr(a, 'summary', ''):
                a.summary = new_summary
                needs_update = True

            if needs_update and a.id is not None:
                db.update_analysis(a.id, {
                    'executive_summary': a.executive_summary,
                    'key_points': a.key_points,
                    'insights': a.insights,
                    'risks': a.risks,
                    'opportunities': a.opportunities,
                    'sources': a.sources,
                    'structured_data': a.structured_data,
                    'geopolitical_analysis': a.geopolitical_analysis,
                    'economic_indicators': a.economic_indicators,
                    'summary': a.summary,
                    'worker_status': getattr(a, 'worker_status', 'completed') or 'completed',
                    'processing_time_seconds': getattr(a, 'processing_time_seconds', 0) or 0,
                })
                fixed += 1
        except Exception as e:
            logger.warning(f"Réparation échouée pour ID {getattr(a, 'id', '?')}: {e}")
            continue

    logger.info(f"Réparation terminée. Enregistrements mis à jour: {fixed}")


if __name__ == '__main__':
    run()


