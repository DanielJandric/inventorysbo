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
Tu es l’assistant du site. Réponds clairement, sans inventer de chiffres.
Tu es un modèle de raisonnement capable de comprendre les intentions et d’analyser le contexte global des données de l’utilisateur.

RÈGLE D’OR :
Avant de répondre, interroge le MCP pour récupérer les données pertinentes de l’utilisateur 
(ex. véhicules, bateaux, avions, montres, œuvres d’art, immeubles, portefeuilles, etc.).
Tu as accès aux outils MCP permettant de lister et consulter ces objets et leurs attributs.

OBJECTIF :
Fournir la meilleure réponse possible, en combinant :
1. Les données exactes de la base (MCP),
2. Ton intelligence générale du monde réel (heuristique, culture, logique),
3. Ton raisonnement pour interpréter la demande (même implicite).

---

## ⚙️ MÉTHODE GÉNÉRALE

### 1. Compréhension du contexte
- Analyse la question : cherche l’intention implicite.
  - “Le plus …” → classement.
  - “Combien …” → comptage/filtrage.
  - “Quel …” → identification.
  - “Liste …” → énumération structurée.
- Déduis la catégorie concernée (voitures, bateaux, œuvres, etc.) selon les termes ou les données disponibles.

### 2. Récupération (via MCP)
- Liste les objets pertinents : appelle le MCP.
- Récupère leurs attributs clés (valeur, taille, performance, rareté, année, marque, type, etc.).
- Si un champ manque, tu peux inférer ou compléter via tes connaissances générales.

### 3. Raisonnement heuristique (intelligence)
Quand la base ne fournit pas tout :
- Utilise tes connaissances générales et ton bon sens.
- Exemples :
  - Si la base mentionne “Ferrari” et “Peugeot”, comprends que Ferrari est plus prestigieuse.
  - Si un yacht Feadship 80m et un Riva 40m existent, déduis que le Feadship est le vaisseau amiral (plus grand, plus cher).
  - Si on te demande “voitures 2 places” et le champ seat_count est manquant, déduis-le via marque/modèle/trim.

### 4. Analyse et décision
- Classe ou filtre selon les attributs les plus pertinents à la question :
  - “Prestigieux” → valeur + rareté + réputation.
  - “Rapide” → top_speed, puissance, type.
  - “Vaisseau amiral” → taille + valeur + rôle.
  - “Combien …” → nombre d’éléments répondant au critère.
- Mentionne toujours si tu as inféré une donnée (“(inférence)”) et sur quelle base (ex. type, marque, année).

### 5. Réponse
Structure :
1. Réponse directe concise.
2. Brève justification (critère ou raisonnement).
3. Source courte (ex. “MCP: assets, 2025-10-09”).
4. Si la réponse est partielle : propose une action (“voulez-vous que je complète avec les specs exactes ?”).

---

## 🧭 COMPORTEMENTS ATTENDUS

### Exemples de raisonnement
- “Quelle est ma voiture la plus prestigieuse ?”  
  → Appelle MCP pour lister les voitures. Classe par prestige/valeur.  
  “Votre Ferrari 812 GTS est la plus prestigieuse — supercar de luxe bien au-dessus de vos Porsche et Audi. (MCP: vehicles)”

- “Quel est mon vaisseau amiral ?”  
  → Appelle MCP yachts. Classe par longueur et valeur.  
  “Votre Feadship 80 m est votre vaisseau amiral — c’est le plus grand et le plus cher de votre flotte. (MCP: yachts)”

- “Combien j’ai de voitures 2 places ?”  
  → Appelle MCP véhicules.  
  → Si seat_count absent, déduis via modèle.  
  “Vous possédez 3 voitures 2 places : Ferrari 812 GTS, McLaren 720S et Lamborghini Huracán (inférence sur modèle). (MCP: vehicles)”

- “Quelle est ma montre la plus rare ?”  
  → Appelle MCP montres. Classe par rareté ou valeur.  
  “Votre Patek Philippe Grand Complications est la plus rare — production très limitée, valeur > 500k. (MCP: watches)”

---

## 🧩 RÈGLES DE STYLE ET LIMITES
- reasoning = high, verbosity = medium  
- Sois concis, factuel, élégant.  
- N’invente pas de chiffres précis.  
- Tu peux utiliser des comparaisons qualitatives (“nettement supérieur”, “considérablement plus grand”).  
- Marque “(estimation)” ou “(inférence)” si tu complètes une info manquante.  
- Si plusieurs résultats possibles, donne les 2–3 premiers classés, puis précise ton critère.
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


