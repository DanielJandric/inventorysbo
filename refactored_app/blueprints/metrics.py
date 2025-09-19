from __future__ import annotations

from flask import Blueprint, jsonify
from ..config import AppConfig
from ..services.ai_engine import AIEngine


bp = Blueprint("metrics", __name__)


@bp.get("/metrics")
def metrics():
    cfg = AppConfig.from_env()
    ai = AIEngine.from_config(cfg)
    return jsonify({
        "success": True,
        "metrics": {
            "openai": "connected" if ai.is_available else "disconnected",
            "model": ai.model if ai.model else None,
            "always_llm": cfg.ALWAYS_LLM,
        }
    })

