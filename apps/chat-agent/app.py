import os
import json
import httpx
import asyncio
import logging
from flask import Flask, request, jsonify, send_from_directory
from supabase import create_client

# Agents SDK (Python)
from agents import Agent, Runner, ModelSettings
from openai.types.shared import Reasoning


# --- Config externes ---
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")  # optionnel
MCP_SERVER_TOKEN = os.getenv("MCP_SERVER_TOKEN")  # optionnel (Authorization: Bearer ...)
MCP_SERVER_HEADERS = os.getenv("MCP_SERVER_HEADERS")  # optionnel (JSON dict)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, static_url_path="", static_folder="static")

# Logging de base (stdout pour Render)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


# --- Helpers Supabase ---
def ensure_chat(chat_id: str | None) -> str:
    if chat_id:
        return chat_id
    res = supabase.table("chats").insert({"title": "New chat"}).execute()
    return res.data[0]["id"]


def save_message(chat_id: str, role: str, content: str):
    supabase.table("messages").insert(
        {"chat_id": chat_id, "role": role, "content": content}
    ).execute()


# --- Agent factory (GPT-5 + MCP) ---
def make_agent() -> Agent:
    return Agent(
        name="Site Assistant",
        instructions=(
            "Tu es l’assistant du site. Réponds clairement, cite si utile. "
            "Utilise les outils MCP quand c’est pertinent. N'invente pas de chiffres: privilégie les données MCP."
        ),
        model="gpt-5",
        model_settings=ModelSettings(
            reasoning=Reasoning(effort="high"),  # reasoning high
            verbosity="medium",                   # verbosity medium
        ),
    )


async def run_with_mcp(prompt: str) -> str:
    # Agent avec HostedMCPTool (le serveur expose /tools et POST d'invocation)
    tools = []  # Désactivé: HostedMCPTool (évite 424 tool-list)

    agent = Agent(
        name="Site Assistant",
        instructions=(
            "Tu es l’assistant du site. Réponds clairement, cite si utile. "
            "Utilise en priorité le pré-contexte fourni (résumé/top). N'invente pas de chiffres. "
            "Pour 'ma voiture la plus prestigieuse', si top_by_value_cars est présent, réponds avec l’entrée en tête (nom + valeur). "
            "Sinon, demande une confirmation pour lancer une recherche détaillée."
        ),
        model="gpt-5",
        model_settings=ModelSettings(
            reasoning=Reasoning(effort="high"),
            verbosity="medium",
        ),
        tools=tools,
    )
    try:
        return (await Runner.run(agent, prompt)).final_output or ""
    except Exception:
        logger.exception("mcp_hosted_failed")
        # Fallback sans MCP
        agent2 = make_agent()
        return (await Runner.run(agent2, prompt)).final_output or ""


def fetch_inventory_overview() -> dict | None:
    """Pré-contexte minimal: résumé + top par valeur (hors vendus) via MCP HTTP.
    Retourne un petit JSON sérialisable ou None si indisponible.
    """
    if not MCP_SERVER_URL:
        return None
    base = MCP_SERVER_URL.rstrip('/')
    try:
        client = httpx.Client(timeout=10.0)
        # 1) Résumé
        r1 = client.post(f"{base}/mcp", json={"tool": "items.summary", "input": {}})
        r1.raise_for_status()
        j1 = r1.json()
        summary = (j1 or {}).get("result") or {}

        # 2) Top valeur (hors vendus)
        search_body_all = {
            "page": 1,
            "page_size": 15,
            "sort": "current_value_desc",
            "filters": {"exclude_sold": True},
        }
        r2 = client.post(f"{base}/mcp", json={"tool": "items.search", "input": search_body_all})
        r2.raise_for_status()
        j2 = r2.json()
        items = ((j2 or {}).get("result") or {}).get("items") or []

        # 3) Top valeur (hors vendus) restreint aux voitures si le champ category existe
        top_cars = []
        try:
            search_body_cars = {
                "page": 1,
                "page_size": 15,
                "sort": "current_value_desc",
                "filters": {"exclude_sold": True, "category": "Voitures"},
            }
            r3 = client.post(f"{base}/mcp", json={"tool": "items.search", "input": search_body_cars})
            if r3.status_code == 200:
                j3 = r3.json()
                top_cars = ((j3 or {}).get("result") or {}).get("items") or []
        except Exception:
            pass
        # Ne garder qu'un sous-ensemble de champs pertinents pour le contexte
        slim = []
        for it in items:
            slim.append({
                "id": it.get("id"),
                "brand": it.get("brand"),
                "model": it.get("model"),
                "year": it.get("construction_year"),
                "value": it.get("current_value"),
                "sale_status": it.get("sale_status"),
            })
        def slim_fields(rows):
            out = []
            for it in rows:
                out.append({
                    "id": it.get("id"),
                    "name": it.get("name"),
                    "category": it.get("category"),
                    "year": it.get("construction_year"),
                    "value": it.get("current_value"),
                    "sale_status": it.get("sale_status"),
                })
            return out

        top_cars_slim = slim_fields(top_cars)
        return {"summary": summary, "top_by_value": slim, "top_by_value_cars": top_cars_slim}
    except Exception:
        logger.exception("inventory_overview_failed")
        return None


@app.route("/chat", methods=["POST"])
def chat():
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
        # Pré-contexte inventaire (vue d'ensemble) injecté avant la question
        overview = fetch_inventory_overview()
        if overview:
            try:
                ctx_json = json.dumps(overview, ensure_ascii=False)
                prefixed = (
                    "[Contexte inventaire - aperçu]\n" + ctx_json + "\n\n"
                    "[Question]\n" + user_msg
                )
                user_payload = prefixed
            except Exception:
                logger.exception("overview_serialize_failed")
                user_payload = user_msg
        else:
            user_payload = user_msg

        # Run l’agent (synchrone via asyncio.run le temps d’une requête)
        assistant_msg = asyncio.run(run_with_mcp(user_payload))
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


