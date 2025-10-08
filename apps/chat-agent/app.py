import os
import asyncio
import logging
from flask import Flask, request, jsonify, send_from_directory
from supabase import create_client

# Agents SDK (Python)
from agents import Agent, Runner, HostedMCPTool, ModelSettings
from openai.types.shared import Reasoning


# --- Config externes ---
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")  # optionnel

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
    tools = []
    if MCP_SERVER_URL:
        tools.append(
            HostedMCPTool(
                tool_config={
                    "type": "mcp",
                    "server_label": "inventory_mcp",
                    "server_url": MCP_SERVER_URL,
                    "require_approval": "never",
                }
            )
        )
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
        tools=tools,
    )


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
        agent = make_agent()
        # Run l’agent (synchrone via asyncio.run le temps d’une requête)
        result = asyncio.run(Runner.run(agent, user_msg))
        assistant_msg = result.final_output or ""
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


