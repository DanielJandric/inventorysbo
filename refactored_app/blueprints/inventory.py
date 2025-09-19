from __future__ import annotations

from flask import Blueprint, jsonify, request
from ..config import AppConfig
from ..services.chatbot_service import ChatbotService
from ..services.ai_engine import AIEngine
from ..repositories.items_repo import ItemsRepository


bp = Blueprint("inventory", __name__)


def _svc() -> ChatbotService:
    cfg = AppConfig.from_env()
    ai = AIEngine.from_config(cfg)
    repo = ItemsRepository.from_config(cfg)
    return ChatbotService(cfg, ai, repo)


@bp.post("/chatbot")
def chatbot():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        session_id = (data.get("session_id") or "").strip() or None
        if not message:
            return jsonify({"error": "Message requis"}), 400

        res = _svc().handle_message(message, session_id=session_id)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

