"""
Routes Flask pour le module SNB Policy Engine

Endpoints:
- POST /api/snb/ingest/cpi
- POST /api/snb/ingest/kof
- POST /api/snb/ingest/snb-forecast
- POST /api/snb/ingest/ois
- POST /api/snb/model/run
- GET  /api/snb/model/latest
- POST /api/snb/explain
"""

import os
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify
from snb_policy_engine import (
    run_model,
    model_output_to_dict,
    parse_ois_points_from_db,
    OISPoint
)

# Import OpenAI (adapté selon votre setup existant)
OPENAI_AVAILABLE = False
openai_client = None

try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        openai_client = OpenAI(api_key=api_key)
        OPENAI_AVAILABLE = True
    else:
        print("WARNING: OpenAI API key not configured")
except Exception as e:
    print(f"WARNING: OpenAI not available: {e}")
    OPENAI_AVAILABLE = False

# Blueprint Flask
snb_bp = Blueprint('snb', __name__, url_prefix='/api/snb')

# === HELPERS ===

def get_supabase_client():
    """Récupère le client Supabase depuis app context"""
    from flask import current_app
    return current_app.config.get('SUPABASE_CLIENT')


def validate_idempotency_key(table_name: str, idempotency_key: str) -> bool:
    """
    Vérifie si l'idempotency_key existe déjà
    
    Returns:
        True si déjà existant (409), False sinon
    """
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        result = supabase.table(table_name).select("id").eq("idempotency_key", idempotency_key).execute()
        return len(result.data) > 0
    except Exception:
        return False


# === ENDPOINTS INGESTION ===

@snb_bp.route('/ingest/cpi', methods=['POST'])
def ingest_cpi():
    """
    POST /api/snb/ingest/cpi
    
    Body: {
        "provider": "BFS",
        "as_of": "2025-08-31",
        "yoy_pct": 0.2,
        "mm_pct": -0.1,
        "source_url": "https://...",
        "idempotency_key": "bfs-2025-08"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body"}), 400
        
        # Validation
        required = ["as_of", "yoy_pct", "idempotency_key"]
        for field in required:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        # Insert dans Supabase (upsert pour éviter duplicates)
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        result = supabase.table("snb_cpi_data").upsert({
            "provider": data.get("provider", "BFS"),
            "as_of": data["as_of"],
            "yoy_pct": data["yoy_pct"],
            "mm_pct": data.get("mm_pct"),
            "source_url": data.get("source_url"),
            "idempotency_key": data["idempotency_key"]
        }, on_conflict="idempotency_key").execute()
        
        return jsonify({"success": True, "id": result.data[0]["id"]}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@snb_bp.route('/ingest/kof', methods=['POST'])
def ingest_kof():
    """
    POST /api/snb/ingest/kof
    
    Body: {
        "provider": "KOF",
        "as_of": "2025-08-01",
        "barometer": 97.4,
        "source_url": "https://...",
        "idempotency_key": "kof-2025-08"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body"}), 400
        
        required = ["as_of", "barometer", "idempotency_key"]
        for field in required:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        result = supabase.table("snb_kof_data").upsert({
            "provider": data.get("provider", "KOF"),
            "as_of": data["as_of"],
            "barometer": data["barometer"],
            "source_url": data.get("source_url"),
            "idempotency_key": data["idempotency_key"]
        }, on_conflict="idempotency_key").execute()
        
        return jsonify({"success": True, "id": result.data[0]["id"]}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@snb_bp.route('/ingest/snb-forecast', methods=['POST'])
def ingest_snb_forecast():
    """
    POST /api/snb/ingest/snb-forecast
    
    Body: {
        "meeting_date": "2025-09-25",
        "forecast": {"2025": 0.2, "2026": 0.5, "2027": 0.7},
        "source_url": "https://...",
        "pdf_url": "https://...",
        "idempotency_key": "snb-mpa-2025-09"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body"}), 400
        
        required = ["meeting_date", "forecast", "idempotency_key"]
        for field in required:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        result = supabase.table("snb_forecasts").upsert({
            "meeting_date": data["meeting_date"],
            "forecast": json.dumps(data["forecast"]),
            "source_url": data.get("source_url"),
            "pdf_url": data.get("pdf_url"),
            "idempotency_key": data["idempotency_key"]
        }, on_conflict="idempotency_key").execute()
        
        return jsonify({"success": True, "id": result.data[0]["id"]}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@snb_bp.route('/ingest/ois', methods=['POST'])
def ingest_ois():
    """
    POST /api/snb/ingest/ois
    
    Body: {
        "as_of": "2025-09-30",
        "points": [
            {"tenor_months": 3, "rate_pct": 0.00},
            {"tenor_months": 6, "rate_pct": 0.01},
            ...
        ],
        "source_url": "https://...",
        "idempotency_key": "ois-2025-09-30"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body"}), 400
        
        required = ["as_of", "points", "idempotency_key"]
        for field in required:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        if len(data["points"]) < 3:
            return jsonify({"success": False, "error": "At least 3 OIS points required"}), 400
        
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        # Upsert (insert ou update si existe déjà)
        result = supabase.table("snb_ois_data").upsert({
            "as_of": data["as_of"],
            "points": json.dumps(data["points"]),
            "source_url": data.get("source_url"),
            "idempotency_key": data["idempotency_key"]
        }, on_conflict="as_of").execute()
        
        return jsonify({"success": True, "id": result.data[0]["id"]}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@snb_bp.route('/ingest/neer', methods=['POST'])
def ingest_neer():
    """
    POST /api/snb/ingest/neer
    
    Body: {
        "as_of": "2025-09-30",
        "neer_value": 100.5,
        "neer_change_3m_pct": -1.2,
        "source_url": "https://data.snb.ch",
        "idempotency_key": "neer-2025-09"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body"}), 400
        
        required = ["as_of", "neer_change_3m_pct", "idempotency_key"]
        for field in required:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        # Upsert dans snb_config avec la clé neer_latest
        supabase.table("snb_config").upsert({
            "key": "neer_latest",
            "value": json.dumps({
                "as_of": data["as_of"],
                "neer_value": data.get("neer_value", 100.0),
                "neer_change_3m_pct": data["neer_change_3m_pct"],
                "source_url": data.get("source_url"),
                "idempotency_key": data["idempotency_key"]
            })
        }).execute()
        
        return jsonify({"success": True, "message": "NEER updated"}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# === ENDPOINTS MODÈLE ===

@snb_bp.route('/model/run', methods=['POST'])
def model_run():
    """
    POST /api/snb/model/run
    
    Body: {
        "overrides": {
            "neer_change_3m_pct": -1.5,  // optionnel
            "cpi_yoy_pct": 0.4,          // optionnel
            "kof_barometer": 96.8,       // optionnel
            "policy_rate_now_pct": 0.0   // optionnel
        }
    }
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        # Récupérer les dernières données
        cpi_data = supabase.table("snb_cpi_data").select("*").order("as_of", desc=True).limit(1).execute()
        kof_data = supabase.table("snb_kof_data").select("*").order("as_of", desc=True).limit(1).execute()
        snb_data = supabase.table("snb_forecasts").select("*").order("meeting_date", desc=True).limit(1).execute()
        ois_data = supabase.table("snb_ois_data").select("*").order("as_of", desc=True).limit(1).execute()
        
        if not (cpi_data.data and kof_data.data and snb_data.data and ois_data.data):
            return jsonify({"success": False, "error": "Insufficient data (missing CPI/KOF/SNB/OIS)"}), 400
        
        # Parse les données
        cpi = cpi_data.data[0]
        kof = kof_data.data[0]
        snb = snb_data.data[0]
        ois = ois_data.data[0]
        
        # Parse forecast (JSON ou dict)
        snb_forecast = snb["forecast"]
        if isinstance(snb_forecast, str):
            snb_forecast = json.loads(snb_forecast)
        
        # Parse OIS points
        ois_points = parse_ois_points_from_db(ois)
        
        # Overrides depuis request
        data = request.get_json() or {}
        overrides = data.get("overrides", {})
        
        cpi_yoy = overrides.get("cpi_yoy_pct", cpi["yoy_pct"])
        kof_bar = overrides.get("kof_barometer", kof["barometer"])
        neer = overrides.get("neer_change_3m_pct", 0.0)
        
        # Policy rate actuel (depuis config ou override)
        policy_config = supabase.table("snb_config").select("value").eq("key", "policy_rate_now_pct").execute()
        policy_rate_now = 0.0
        if policy_config.data:
            policy_value = policy_config.data[0]["value"]
            if isinstance(policy_value, (int, float)):
                policy_rate_now = float(policy_value)
            elif isinstance(policy_value, str):
                policy_rate_now = float(policy_value)
        policy_rate_now = overrides.get("policy_rate_now_pct", policy_rate_now)
        
        # NEER (depuis config ou override)
        neer_config = supabase.table("snb_config").select("value").eq("key", "neer_latest").execute()
        neer_from_db = 0.0
        if neer_config.data:
            neer_value = neer_config.data[0]["value"]
            if isinstance(neer_value, str):
                neer_value = json.loads(neer_value)
            if isinstance(neer_value, dict):
                neer_from_db = float(neer_value.get("neer_change_3m_pct", 0.0))
        neer = overrides.get("neer_change_3m_pct", neer if neer != 0.0 else neer_from_db)
        
        # Run modèle
        result = run_model(
            cpi_yoy=float(cpi_yoy),
            kof=float(kof_bar),
            snb_forecast=snb_forecast,
            ois_points=ois_points,
            policy_rate_now=float(policy_rate_now),
            neer_change_3m=float(neer),
            as_of_date=date.fromisoformat(ois["as_of"])
        )
        
        # Sauvegarder dans snb_model_runs
        output_dict = model_output_to_dict(result)
        supabase.table("snb_model_runs").insert({
            "as_of": output_dict["as_of"],
            "inputs": json.dumps(output_dict["inputs"]),
            "nowcast": json.dumps(output_dict["nowcast"]),
            "output_gap_pct": output_dict["output_gap_pct"],
            "i_star_next_pct": output_dict["i_star_next_pct"],
            "probs": json.dumps(output_dict["probs"]),
            "path": json.dumps(output_dict["path"]),
            "version": output_dict["version"]
        }).execute()
        
        return jsonify({"success": True, "result": output_dict}), 200
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@snb_bp.route('/model/latest', methods=['GET'])
def model_latest():
    """
    GET /api/snb/model/latest
    
    Retourne le dernier run du modèle
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        result = supabase.table("snb_model_runs").select("*").order("created_at", desc=True).limit(1).execute()
        
        if not result.data:
            return jsonify({"success": False, "error": "No model run found"}), 404
        
        run = result.data[0]
        
        # Parse JSONB fields
        output = {
            "as_of": run["as_of"],
            "inputs": json.loads(run["inputs"]) if isinstance(run["inputs"], str) else run["inputs"],
            "nowcast": json.loads(run["nowcast"]) if isinstance(run["nowcast"], str) else run["nowcast"],
            "output_gap_pct": run["output_gap_pct"],
            "i_star_next_pct": run["i_star_next_pct"],
            "probs": json.loads(run["probs"]) if isinstance(run["probs"], str) else run["probs"],
            "path": json.loads(run["path"]) if isinstance(run["path"], str) else run["path"],
            "version": run["version"]
        }
        
        return jsonify({"success": True, "result": output}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# === ENDPOINT EXPLICATION GPT-5 ===

@snb_bp.route('/explain', methods=['POST'])
def explain_model():
    """
    POST /api/snb/explain
    
    Lance l'explication GPT-5 en background via Celery (évite timeout worker)
    
    Body: {
        "model": { ... le JSON de /model/latest ... },
        "tone": "concise",
        "lang": "fr-CH"
    }
    
    Retourne task_id pour polling (HTTP 202) ou résultat direct si rapide
    """
    try:
        from snb_tasks import snb_explain_task
        
        data = request.get_json()
        if not data or "model" not in data:
            return jsonify({"success": False, "error": "Missing 'model' field"}), 400
        
        model_json = data["model"]
        tone = data.get("tone", "concise")
        lang = data.get("lang", "fr-CH")
        
        # Lancer la tâche GPT-5 en background (évite timeout)
        task = snb_explain_task.delay(model_json, tone, lang)
        
        return jsonify({
            "success": True,
            "message": "Explication GPT-5 en cours de generation (background)",
            "task_id": task.id,
            "status_url": f"/api/snb/explain/status/{task.id}"
        }), 202
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@snb_bp.route('/explain/status/<task_id>', methods=['GET'])
def get_explain_status(task_id):
    """
    GET /api/snb/explain/status/<task_id>
    
    Vérifie le statut d'une tâche d'explication GPT-5
    """
    try:
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                "state": task.state,
                "status": "En attente..."
            }
        elif task.state == 'PROGRESS':
            response = {
                "state": task.state,
                "status": "GPT-5 en cours de raisonnement...",
                "meta": task.info
            }
        elif task.state == 'SUCCESS':
            result = task.info
            response = {
                "state": task.state,
                "status": "Terminé",
                "success": result.get("success"),
                "explanation": result.get("explanation"),
                "tokens": result.get("tokens")
            }
        else:  # FAILURE
            response = {
                "state": task.state,
                "status": "Erreur",
                "error": str(task.info)
            }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# === ENDPOINTS UTILITAIRES ===

@snb_bp.route('/data/summary', methods=['GET'])
def data_summary():
    """
    GET /api/snb/data/summary
    
    Retourne un résumé des données disponibles
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        cpi_count = supabase.table("snb_cpi_data").select("id", count="exact").execute()
        kof_count = supabase.table("snb_kof_data").select("id", count="exact").execute()
        snb_count = supabase.table("snb_forecasts").select("id", count="exact").execute()
        ois_count = supabase.table("snb_ois_data").select("id", count="exact").execute()
        runs_count = supabase.table("snb_model_runs").select("id", count="exact").execute()
        
        summary = {
            "cpi_data_count": cpi_count.count if hasattr(cpi_count, 'count') else len(cpi_count.data),
            "kof_data_count": kof_count.count if hasattr(kof_count, 'count') else len(kof_count.data),
            "snb_forecasts_count": snb_count.count if hasattr(snb_count, 'count') else len(snb_count.data),
            "ois_data_count": ois_count.count if hasattr(ois_count, 'count') else len(ois_count.data),
            "model_runs_count": runs_count.count if hasattr(runs_count, 'count') else len(runs_count.data)
        }
        
        return jsonify({"success": True, "summary": summary}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# === ENDPOINT TRIGGER MANUEL ===

@snb_bp.route('/trigger/collect', methods=['POST'])
def trigger_manual_collection():
    """
    POST /api/snb/trigger/collect
    
    Lance manuellement la collecte de données via Celery background worker
    
    Body: {
        "mode": "daily" | "monthly" | "quarterly" | "all"
    }
    """
    try:
        data = request.get_json() or {}
        mode = data.get("mode", "monthly")
        
        # Import de la tâche Celery
        from snb_tasks import snb_collect_task
        
        # Lancer la tâche en background (non-bloquant)
        task = snb_collect_task.delay(mode)
        
        return jsonify({
            "success": True,
            "message": f"Collecte {mode} lancee en background",
            "task_id": task.id,
            "status_url": f"/api/snb/trigger/status/{task.id}"
        }), 202
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@snb_bp.route('/trigger/status/<task_id>', methods=['GET'])
def get_collection_status(task_id):
    """
    GET /api/snb/trigger/status/<task_id>
    
    Vérifie le statut d'une tâche de collecte
    """
    try:
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                "state": task.state,
                "status": "En attente..."
            }
        elif task.state == 'PROGRESS':
            response = {
                "state": task.state,
                "status": "En cours...",
                "meta": task.info
            }
        elif task.state == 'SUCCESS':
            response = {
                "state": task.state,
                "status": "Terminé",
                "result": task.info
            }
        else:  # FAILURE
            response = {
                "state": task.state,
                "status": "Erreur",
                "error": str(task.info)
            }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

