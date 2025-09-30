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
        
        # Idempotence check
        if validate_idempotency_key("snb_cpi_data", data["idempotency_key"]):
            return jsonify({"success": False, "error": "Idempotency key already exists"}), 409
        
        # Insert dans Supabase
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        result = supabase.table("snb_cpi_data").insert({
            "provider": data.get("provider", "BFS"),
            "as_of": data["as_of"],
            "yoy_pct": data["yoy_pct"],
            "mm_pct": data.get("mm_pct"),
            "source_url": data.get("source_url"),
            "idempotency_key": data["idempotency_key"]
        }).execute()
        
        return jsonify({"success": True, "id": result.data[0]["id"]}), 201
    
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
        
        if validate_idempotency_key("snb_kof_data", data["idempotency_key"]):
            return jsonify({"success": False, "error": "Idempotency key already exists"}), 409
        
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        result = supabase.table("snb_kof_data").insert({
            "provider": data.get("provider", "KOF"),
            "as_of": data["as_of"],
            "barometer": data["barometer"],
            "source_url": data.get("source_url"),
            "idempotency_key": data["idempotency_key"]
        }).execute()
        
        return jsonify({"success": True, "id": result.data[0]["id"]}), 201
    
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
        
        if validate_idempotency_key("snb_forecasts", data["idempotency_key"]):
            return jsonify({"success": False, "error": "Idempotency key already exists"}), 409
        
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        result = supabase.table("snb_forecasts").insert({
            "meeting_date": data["meeting_date"],
            "forecast": json.dumps(data["forecast"]),
            "source_url": data.get("source_url"),
            "pdf_url": data.get("pdf_url"),
            "idempotency_key": data["idempotency_key"]
        }).execute()
        
        return jsonify({"success": True, "id": result.data[0]["id"]}), 201
    
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
        
        if validate_idempotency_key("snb_ois_data", data["idempotency_key"]):
            return jsonify({"success": False, "error": "Idempotency key already exists"}), 409
        
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({"success": False, "error": "Supabase not available"}), 500
        
        result = supabase.table("snb_ois_data").insert({
            "as_of": data["as_of"],
            "points": json.dumps(data["points"]),
            "source_url": data.get("source_url"),
            "idempotency_key": data["idempotency_key"]
        }).execute()
        
        return jsonify({"success": True, "id": result.data[0]["id"]}), 201
    
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
    
    Body: {
        "model": { ... le JSON de /model/latest ... },
        "tone": "concise",
        "lang": "fr-CH"
    }
    
    Retourne: {
        "headline": "...",
        "bullets": ["...", "...", "..."],
        "risks": ["...", "..."],
        "next_steps": ["...", "..."],
        "one_liner": "..."
    }
    """
    try:
        if not OPENAI_AVAILABLE:
            return jsonify({"success": False, "error": "OpenAI not configured"}), 503
        
        data = request.get_json()
        if not data or "model" not in data:
            return jsonify({"success": False, "error": "Missing 'model' field"}), 400
        
        model_json = data["model"]
        tone = data.get("tone", "concise")
        lang = data.get("lang", "fr-CH")
        
        # Prompt système
        system_prompt = f"""Tu es un stratégiste de banque centrale spécialisé dans la politique monétaire suisse.

Explique en {lang} les résultats du modèle BNS en 5 éléments structurés:
- headline: Titre principal (max 80 caractères)
- bullets: 3-5 points clés explicatifs
- risks: 2-4 risques identifiés
- next_steps: 2-3 actions de suivi
- one_liner: Synthèse ultra-concise (max 140 caractères)

Réponds STRICTEMENT en JSON avec ces clés. Ton ton est {tone} et professionnel.
"""
        
        user_prompt = f"Voici le JSON du modèle:\n{json.dumps(model_json, indent=2)}"
        
        # Appel OpenAI (adaptez selon votre version)
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # ou "gpt-5-pro" si disponible
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        explanation = json.loads(response.choices[0].message.content)
        
        return jsonify({"success": True, "explanation": explanation}), 200
    
    except Exception as e:
        import traceback
        traceback.print_exc()
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

