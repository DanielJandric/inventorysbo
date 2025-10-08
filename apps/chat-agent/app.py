import os
import json
import asyncio
import logging
from flask import Flask, request, jsonify, send_from_directory
from supabase import create_client

# Agents SDK (Python)
from agents import Agent, Runner, ModelSettings
from agents.mcp import MCPServerStreamableHttp
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
    if not MCP_SERVER_URL:
        # Pas de MCP configuré: agent sans serveur MCP
        agent = make_agent()
        return (await Runner.run(agent, prompt)).final_output or ""

    try:
        # Construit les headers MCP optionnels
        headers: dict | None = None
        try:
            extra = json.loads(MCP_SERVER_HEADERS) if MCP_SERVER_HEADERS else None
            if MCP_SERVER_TOKEN or extra:
                headers = {}
                if MCP_SERVER_TOKEN:
                    headers["Authorization"] = f"Bearer {MCP_SERVER_TOKEN}"
                if isinstance(extra, dict):
                    headers.update({str(k): str(v) for k, v in extra.items()})
        except Exception:
            logger.exception("invalid_mcp_headers_json")

        async with MCPServerStreamableHttp(
            name="inventory_mcp_stream",
            params={
                "url": MCP_SERVER_URL,
                "timeout": 20,
                **({"headers": headers} if headers else {}),
            },
            cache_tools_list=True,
        ) as server:
            agent = Agent(
                name="Site Assistant",
                instructions=(
                    "Tu es l’assistant du site. Réponds clairement, cite si utile. "
                    "Utilise les outils MCP quand c’est pertinent. N'invente pas de chiffres: privilégie les données MCP."
                ),
                model="gpt-5",
                model_settings=ModelSettings(
                    reasoning=Reasoning(effort="high"),
                    verbosity="medium",
                ),
                mcp_servers=[server],
            )
            return (await Runner.run(agent, prompt)).final_output or ""
    except Exception as e:
        logger.exception("mcp_connect_failed")
        # Fallback sans MCP
        agent = make_agent()
        return (await Runner.run(agent, prompt)).final_output or ""


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
        # Run l’agent (synchrone via asyncio.run le temps d’une requête)
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


