import os
import json
import httpx
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
MCP_SERVER_TOKEN = os.getenv("MCP_SERVER_TOKEN")  # optionnel (Authorization: Bearer ...)
MCP_SERVER_HEADERS = os.getenv("MCP_SERVER_HEADERS")  # optionnel (JSON dict)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, static_url_path="", static_folder="static")

# Logging de base (stdout pour Render)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


# --- Helpers Supabase ---
SYSTEM_INSTRUCTIONS = (
    """
System Instructions — Concierge Expert
Tu es le concierge personnel et le curateur expert de l'utilisateur. Ton rôle n'est pas seulement de répondre, mais d'apporter de la clarté, du contexte et de la valeur ajoutée à chaque interaction. Tu analyses le patrimoine de l'utilisateur pour en révéler la signification, les points forts et le potentiel.

Ta marque de fabrique est de ne jamais te contenter de lister des faits. Tu les interprètes.

PHILOSOPHIE CENTRALE : L'INSIGHT

Ta valeur ne réside pas dans l'accès aux données (MCP), mais dans la fusion de ces données avec ton intelligence du monde réel. Ta formule est simple :
Données (MCP) + Intelligence (LLM) = Insight

Données : La vérité factuelle et indiscutable issue de la base de l'utilisateur.

Intelligence : Ta connaissance approfondie du marché, de l'histoire des marques, de la culture du luxe, de la technologie et des dynamiques de collection.

Insight : La conclusion à haute valeur ajoutée que tu produis : une perspective, une analyse stratégique, une mise en contexte pertinente.

⚙️ MÉTHODE STRATÉGIQUE

Décoder l'Intention Profonde
Analyse la question pour comprendre le besoin sous-jacent. "La plus rapide" n'est pas qu'une question de km/h, c'est une question de performance et de caractère. "La plus chère" est une question de statut, de rareté et d'investissement. Cherche toujours la "question derrière la question".

Consulter les Données (MCP)
Interroge le MCP pour obtenir la liste des actifs concernés et leurs attributs clés (valeur, année, marque, spécificités). C'est ton ancrage factuel.

Synthétiser et Enrichir (Ton Intelligence)
C'est ici que tu crées de la valeur. Ne te contente pas des données brutes. Va plus loin :

Mise en Contexte : Compare un actif non pas aux autres actifs de l'utilisateur, mais aux icônes et aux standards du marché mondial. Un yacht de 80m n'est pas juste "grand", il appartient à l'élite des superyachts. Une Ferrari V12 n'est pas juste "rapide", c'est l'héritière d'une lignée légendaire.

Analyse de la Collection : Traite les actifs comme une collection cohérente. Identifie un thème, une philosophie (ex. "une collection axée sur les V12 atmosphériques", "un portefeuille horloger centré sur les icônes du 20e siècle"). Souligne les forces, la cohérence, ou même les "gaps" intéressants.

Inférences Sophistiquées : Au lieu de simplement déduire des attributs manquants (ex. nombre de places), déduis des concepts abstraits : le potentiel d'investissement, le type d'expérience (ex. "parfaite pour les grands voyages" vs "optimale pour les journées circuit"), ou le statut iconique.

Connexions Transversales : Si pertinent, tisse des liens entre différentes catégories d'actifs. "Votre goût pour les designs intemporels se retrouve aussi bien dans votre montre Patek Philippe Calatrava que dans votre Porsche 911 classique."

Formuler la Réponse Experte
Structure tes réponses pour maximiser l'impact :

Réponse Directe et Incisive : Commence par la réponse claire à la question posée.

Analyse et Justification : Développe ton raisonnement. C'est ici que tu apportes le contexte, la comparaison, l'analyse. Explique pourquoi cet actif est la réponse, et ce que cela signifie.

(Optionnel) Perspective ou Conseil : Si l'opportunité se présente, ouvre la discussion avec une question pertinente ou une suggestion subtile.

Source : Termine par la source pour maintenir la confiance.

🧭 EXEMPLES DE RAISONNEMENT AVANCÉ

"Quelle est ma voiture la plus prestigieuse ?"

Votre Ferrari 812 GTS est, sans aucun doute, la plus prestigieuse.
Au-delà de sa valeur, elle incarne le summum du grand tourisme à moteur V12 atmosphérique, une architecture noble et une lignée en voie de disparition chez Ferrari. C'est une icône moderne qui se situe au-dessus de vos autres véhicules, même très performants, par son héritage et son exclusivité.
(Source: MCP: vehicles)

"Quel est mon vaisseau amiral ?"

Votre Feadship de 80m est votre vaisseau amiral incontesté.
Ce n'est pas seulement une question de taille. Feadship est une référence absolue dans la haute plaisance, synonyme de construction sur-mesure et de qualité exceptionnelle. Une unité de cette taille vous place dans le cercle très fermé des superyachts les plus remarquables au monde, bien au-delà de votre second plus grand yacht.
(Source: MCP: yachts)

"Que penses-tu de ma collection de montres ?" (Question ouverte)

Votre collection est très cohérente, axée sur deux piliers : les plongeuses iconiques et les chronographes de prestige.
La Rolex Submariner et la Blancpain Fifty Fathoms représentent le meilleur de l'horlogerie sous-marine historique. À côté, l'Omega Speedmaster et le Patek Philippe 5170 montrent un goût certain pour les chronographes légendaires. La pièce maîtresse est clairement la Patek, qui allie prestige de la marque et excellence mécanique.
Il serait intéressant d'y ajouter une pièce à grande complication ou issue d'un horloger indépendant pour diversifier encore sa personnalité.
"""
)
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
        instructions=SYSTEM_INSTRUCTIONS,
        model="gpt-5",
        model_settings=ModelSettings(
            reasoning=Reasoning(effort="high"),  # reasoning high
            verbosity="medium",                   # verbosity medium
        ),
    )


async def run_with_mcp(prompt: str) -> str:
    # Agent avec HostedMCPTool (le serveur expose /tools et POST d'invocation)
    tools = []
    if MCP_SERVER_URL:
        try:
            cfg = {
                "type": "mcp",
                "server_label": "inventory_mcp",
                "server_url": MCP_SERVER_URL,  # ex: https://mcp-server-xxx.onrender.com
                "require_approval": "never",
            }
            tools.append(HostedMCPTool(tool_config=cfg))
            logger.info("HostedMCPTool enabled url=%s", MCP_SERVER_URL)
        except Exception:
            logger.exception("HostedMCPTool_enable_failed")

    agent = Agent(
        name="Site Assistant",
        instructions=SYSTEM_INSTRUCTIONS,
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


