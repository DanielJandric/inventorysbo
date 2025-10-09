import os
import json
import httpx
import asyncio
import logging
from uuid import uuid4
from flask import Flask, request, jsonify, send_from_directory
from supabase import create_client
from typing import Dict, Optional

# Agents SDK (Python)
from agents import Agent, Runner, HostedMCPTool, ModelSettings
from agents.mcp import MCPServerStreamableHttp
from openai.types.shared import Reasoning


# --- Config externes ---
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")  # optionnel
MCP_SERVER_TOKEN = os.getenv("MCP_SERVER_TOKEN")  # optionnel (Authorization: Bearer ...)
MCP_SERVER_HEADERS = os.getenv("MCP_SERVER_HEADERS")  # optionnel (JSON dict)
_chat_tokens_raw = os.getenv("CHAT_AGENT_API_TOKENS") or os.getenv("CHAT_AGENT_API_TOKEN")
if not _chat_tokens_raw:
    raise RuntimeError("CHAT_AGENT_API_TOKEN (or CHAT_AGENT_API_TOKENS) is required")
CHAT_AGENT_API_TOKENS = {token.strip() for token in _chat_tokens_raw.split(",") if token.strip()}
if not CHAT_AGENT_API_TOKENS:
    raise RuntimeError("CHAT_AGENT_API_TOKEN (or CHAT_AGENT_API_TOKENS) must contain at least one token")
CHAT_AGENT_MODEL = os.getenv("CHAT_AGENT_MODEL", "gpt-5")
CHAT_AGENT_PERSIST = os.getenv("CHAT_AGENT_PERSIST", "true").strip().lower() == "true"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, static_url_path="", static_folder="static")

# Logging de base (stdout pour Render)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def _authorized_request(req_headers: dict) -> bool:
    header = req_headers.get("Authorization", "")
    token = ""
    if isinstance(header, str) and header.startswith("Bearer "):
        token = header[7:].strip()
    elif isinstance(req_headers.get("X-API-Key"), str):
        token = req_headers["X-API-Key"].strip()
    return token in CHAT_AGENT_API_TOKENS


def _build_mcp_headers() -> Optional[Dict[str, str]]:
    headers: Dict[str, str] = {}
    if MCP_SERVER_TOKEN:
        headers["Authorization"] = f"Bearer {MCP_SERVER_TOKEN}"
    if MCP_SERVER_HEADERS:
        try:
            extra = json.loads(MCP_SERVER_HEADERS)
            if isinstance(extra, dict):
                headers.update({str(k): str(v) for k, v in extra.items()})
        except Exception:
            logger.warning("invalid JSON in MCP_SERVER_HEADERS")
    return headers or None




# --- Helpers Supabase ---
SYSTEM_INSTRUCTIONS = (
    """
System Instructions - Concierge Expert
Tu es le concierge personnel et le curateur expert de l'utilisateur. Ta mission est de livrer contexte, analyse et valeur a chaque echange. Tu relies les donnees factuelles du MCP a une lecture experte du marche du luxe.

Philosophie
- Donnees (MCP) + Intelligence (LLM) = Insight.
- Les donnees apportent la verite factuelle, ton intelligence transforme ces faits en perspective strategique.

Methode
1. Identifier l'intention derriere la demande: performance, prestige, rendement ou experience.
2. Interroger le MCP avec precision: selectionner les outils minimaux et justifier chaque appel.
3. Produire une synthese: comparer aux benchmarks mondiaux, expliquer la valeur, signaler les lacunes de la collection et croiser les categories quand cela apporte un insight.
4. Conseiller avec finesse: proposer une interpretation exploitable (opportunite, risque, potentiel d'image) et, si pertinent, ouvrir sur la suite.

Style de reponse
- Debut clair avec la reponse directe.
- Analyse structuree (contexte marche, comparaison, impact pour l'utilisateur).
- Conclusion facultative: question de relance ou recommandation concrete.
- Indication de source MCP en fin de reponse.

Exemples de raisonnement expert
- Voiture la plus prestigieuse: insister sur le pedigree, la rarete et la place dans la collection.
- Vaisseau amiral: relier dimensions, chantier et standing international.
- Evaluation de collection horlogere: decrire les themes dominants, la coherence et les pistes d'enrichissement.
"""
)
def ensure_chat(chat_id: str | None) -> str:
    if chat_id:
        return chat_id
    if not CHAT_AGENT_PERSIST:
        return str(uuid4())
    res = supabase.table("chats").insert({"title": "New chat"}).execute()
    return res.data[0]["id"]


def save_message(chat_id: str, role: str, content: str):
    if not CHAT_AGENT_PERSIST:
        return
    supabase.table("messages").insert(
        {"chat_id": chat_id, "role": role, "content": content}
    ).execute()


# --- Agent factory (GPT-5 + MCP) ---
def make_agent() -> Agent:
    return Agent(
        name="Site Assistant",
        instructions=SYSTEM_INSTRUCTIONS,
        model=CHAT_AGENT_MODEL,
        model_settings=ModelSettings(
            reasoning=Reasoning(effort="high"),  # reasoning high
            verbosity="medium",                   # verbosity medium
        ),
    )


async def run_with_mcp(prompt: str) -> str:
    # Intégration Streamable HTTP MCP (avec headers optionnels)
    if not MCP_SERVER_URL:
        agent = make_agent()
        return (await Runner.run(agent, prompt)).final_output or ""

    headers = _build_mcp_headers()

    try:
        async with MCPServerStreamableHttp(
            name="inventory_mcp",
            params={
                "url": MCP_SERVER_URL,
                **({"headers": headers} if headers else {}),
                "timeout": 20,
            },
            cache_tools_list=True,
        ) as server:
            agent = Agent(
                name="Site Assistant",
                instructions=SYSTEM_INSTRUCTIONS,
                model=CHAT_AGENT_MODEL,
                model_settings=ModelSettings(
                    reasoning=Reasoning(effort="high"),
                    verbosity="medium",
                ),
                mcp_servers=[server],
            )
            return (await Runner.run(agent, prompt)).final_output or ""
    except Exception:
        logger.exception("mcp_stream_failed")
        agent2 = make_agent()
        return (await Runner.run(agent2, prompt)).final_output or ""




def fetch_inventory_overview() -> Optional[dict]:
    """Minimal MCP context: summary + top assets."""
    if not MCP_SERVER_URL:
        return None
    base = MCP_SERVER_URL.rstrip('/')
    headers = _build_mcp_headers()
    client_kwargs: Dict[str, object] = {"timeout": 10.0}
    if headers:
        client_kwargs["headers"] = headers
    try:
        with httpx.Client(**client_kwargs) as client:
            r1 = client.post(f"{base}/mcp", json={"tool": "items.summary", "input": {}})
            r1.raise_for_status()
            summary = (r1.json() or {}).get("result") or {}

            search_body_all = {
                "page": 1,
                "page_size": 15,
                "sort": "current_value_desc",
                "filters": {"exclude_sold": True},
            }
            r2 = client.post(f"{base}/mcp", json={"tool": "items.search", "input": search_body_all})
            r2.raise_for_status()
            j2 = r2.json() or {}
            items = (j2.get("result") or {}).get("items") or []

            top_cars = []
            car_payload = {
                "page": 1,
                "page_size": 15,
                "sort": "current_value_desc",
                "filters": {"exclude_sold": True, "category": "Voitures"},
            }
            try:
                r3 = client.post(f"{base}/mcp", json={"tool": "items.search", "input": car_payload})
                if r3.status_code == 200:
                    j3 = r3.json() or {}
                    top_cars = (j3.get("result") or {}).get("items") or []
            except Exception:
                pass

            def _slim(rows):
                slimmed = []
                for row in rows:
                    slimmed.append(
                        {
                            "id": row.get("id"),
                            "name": row.get("name"),
                            "brand": row.get("brand"),
                            "model": row.get("model"),
                            "category": row.get("category"),
                            "year": row.get("construction_year"),
                            "value": row.get("current_value"),
                            "sale_status": row.get("sale_status"),
                        }
                    )
                return slimmed

            return {
                "summary": summary,
                "top_by_value": _slim(items),
                "top_by_value_cars": _slim(top_cars),
            }
    except Exception:
        logger.exception("inventory_overview_failed")
        return None


@app.route("/chat", methods=["POST"])
def chat():
    if not _authorized_request(request.headers):
        return jsonify({"error": "unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception:
        logger.exception("invalid_json")
        return jsonify({"error": "invalid json"}), 400

    user_msg = (data.get("message") or data.get("input") or "").strip() if isinstance(data, dict) else ""
    chat_id = ensure_chat((data or {}).get("chat_id") if isinstance(data, dict) else None)

    if not user_msg:
        logger.info("chat_request_empty")
        return jsonify({"error": "message manquant"}), 400

    logger.info("chat_request start chat_id=%s len=%d", chat_id, len(user_msg))
    try:
        save_message(chat_id, "user", user_msg)
    except Exception:
        logger.exception("supabase_save_user_failed")

    try:
        assistant_msg = asyncio.run(run_with_mcp(user_msg))
        try:
            save_message(chat_id, "assistant", assistant_msg)
        except Exception:
            logger.exception("supabase_save_assistant_failed")
        logger.info("chat_request done chat_id=%s out_len=%d", chat_id, len(assistant_msg))
        return jsonify({"chat_id": chat_id, "output": assistant_msg})
    except Exception:
        logger.exception("agent_run_failed")
        return jsonify({"error": "agent error"}), 500


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    # Pour local: `python apps/chat-agent/app.py`
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)


