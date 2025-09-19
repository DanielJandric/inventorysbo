from __future__ import annotations

from flask import Blueprint, jsonify, request
from ..config import AppConfig
from ..services.markets_service import MarketsService
from ..services.ai_engine import AIEngine


bp = Blueprint("markets", __name__)


def _svc() -> MarketsService:
    cfg = AppConfig.from_env()
    ai = AIEngine.from_config(cfg)
    return MarketsService(cfg, ai)


@bp.post("/markets/chat")
def markets_chat():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        if not message:
            return jsonify({"success": False, "error": "Message vide"}), 400
        res = _svc().handle_message(message)
        return jsonify({"success": True, **res}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

