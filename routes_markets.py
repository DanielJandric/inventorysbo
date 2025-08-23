"""
Routes pour les fonctionnalités marché (markets)
"""
import os
import time
import json
import uuid
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template, Response

# Import des managers et utilitaires
from managers import conversation_memory, responses_prev_ids
from gpt5_compat import extract_output_text

logger = logging.getLogger(__name__)

# Blueprint pour les routes marché
markets_bp = Blueprint('markets', __name__)

# Variables globales nécessaires (à injecter depuis app.py)
web_search_manager = None
client = None  # OpenAI client


def init_markets_routes(openai_client, web_search_mgr=None):
    """Initialise les routes marché avec les dépendances nécessaires"""
    global client, web_search_manager
    client = openai_client
    web_search_manager = web_search_mgr


@markets_bp.route("/markets")
def markets():
    """Page des updates de marchés financiers"""
    return render_template('markets.html')


@markets_bp.route("/api/markets/chat", methods=["POST"])
def markets_chat():
    """Chatbot marchés: chemin rapide par défaut, RAG/web-search optionnels.
    Entrée JSON: { message: str, context?: str, session_id?: str }
    Sortie JSON: { success: bool, reply?: str, error?: str, metadata?: { session_id } }
    """
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        if not user_message:
            return jsonify({"success": False, "error": "Message vide"}), 400
            
        # Options runtime
        use_rag = bool(data.get("use_rag", False))
        use_web = bool(data.get("use_web", False))
        # Limite stricte à 1 rapport si RAG activé
        try:
            requested_limit = int(data.get("limit", 1)) if use_rag else 0
        except Exception:
            requested_limit = 0
        limit = 1 if requested_limit == 1 else 0
        extra_context = (data.get("context") or "").strip()
        session_id = (data.get("session_id") or "").strip() or str(uuid.uuid4())

        # Récupérer mémoire de session (messages précédents)
        try:
            history_persisted = conversation_memory.get_recent_messages(session_id, limit=2)
        except Exception:
            history_persisted = []

        # Contexte: rapide par défaut; ajouter RAG seulement si demandé
        context_text = ""
        try:
            from market_analysis_db import get_market_analysis_db
            db = get_market_analysis_db()
            recent_items = db.get_recent_analyses(limit=4) if use_rag else []

            # Scoring naïf par recouvrement de mots-clés question/contexte vs contenu des rapports
            import re as _re
            def _tokenize(txt: str) -> set:
                words = _re.findall(r"[\w\-]+", (txt or "").lower())
                return {w for w in words if len(w) >= 3}

            query_terms = _tokenize(user_message + " " + extra_context)

            scored = []
            for a in recent_items:
                try:
                    exec_text = "\n".join(a.executive_summary or []) if a.executive_summary else ""
                    base = f"{exec_text}\n{(a.summary or '')[:1200]}"
                    report_terms = _tokenize(base)
                    score = len(query_terms & report_terms)
                    scored.append((score, a))
                except Exception:
                    continue
            scored.sort(key=lambda x: x[0], reverse=True)
            top_items = [a for _, a in (scored[:limit] if scored else [])]

            # Construire le contexte compact
            context_parts = []
            for a in top_items:
                try:
                    exec_summary = "\n".join([f"- {p}" for p in (a.executive_summary or [])]) if a.executive_summary else ""
                    summary_compact = (a.summary or "")[:800]
                    ts = a.timestamp or a.created_at or ""
                    context_parts.append(
                        f"[Rapport ID {a.id or '?'} | {a.analysis_type or 'auto'} | {ts}]\n"
                        f"Executive Summary:\n{exec_summary}\n"
                        f"Résumé:\n{summary_compact}\n---\n"
                    )
                except Exception:
                    continue
            context_text = "\n".join(context_parts)
            if extra_context:
                context_text = f"Contexte additionnel (utilisateur):\n{extra_context}\n---\n" + context_text
            # Clip du contexte pour éviter timeouts/mémoire
            try:
                if len(context_text) > 2000:
                    context_text = context_text[:2000]
            except Exception:
                pass
        except Exception as _e:
            # Si la BDD ou la désérialisation pose souci, continuer sans contexte
            context_text = (f"Contexte additionnel (utilisateur):\n{extra_context}\n---\n" if extra_context else "")

        # Client OpenAI (GPT-5 pur) avec timeout global
        try:
            from openai import OpenAI
            timeout_s = int(os.getenv('TIMEOUT_S', '60'))
            client = OpenAI(timeout=timeout_s)
        except Exception as e:
            logger.error(f"OpenAI init error: {e}")
            return jsonify({"success": False, "error": "OpenAI non configuré"}), 500

        # Prompt système plus direct, avec mémoire et consignes
        system_prompt = (
            "Tu es un analyste marchés. Réponds en français, de manière concise, actionnable et contextuelle. "
            "Utilise la mémoire de conversation (si pertinente) pour assurer la continuité. "
            "Reconnais patterns (tendance, corrélations, régimes de volatilité) et commente risques/opportunités. "
            "N'invente jamais de chiffres. Utilise **gras** pour les points critiques, et des emojis sobres (↑, ↓, 🟢, 🔴, ⚠️, 💡). "
            "Structure la réponse en 3–5 points maximum, puis une phrase de conclusion claire."
        )

        # Appel Responses API (GPT-5 pur) avec web en texte si demandé
        try:
            ws_text = ""
            if bool(data.get("use_web", False)) and web_search_manager:
                try:
                    from web_search_manager import WebSearchType
                    ws_res = web_search_manager.search_financial_markets(
                        search_type=WebSearchType.MARKET_DATA,
                        search_context_size="low"
                    )
                    if ws_res and getattr(ws_res, 'content', None):
                        ws_text = str(ws_res.content)[:1200]
                except Exception:
                    ws_text = ""

            eff = (os.getenv("AI_REASONING_EFFORT", "high") or "").strip().lower()
            if eff not in ("low", "medium", "high"):
                eff = "high"

            user_parts = []
            if ws_text:
                user_parts.append(f"Contexte (recherche web):\n{ws_text}\n---\n")
            if context_text:
                user_parts.append(f"Contexte (rapports):\n{context_text}\n\n")
            user_parts.append(f"Question: {user_message}")
            user_prompt_final = "".join(user_parts)

            max_out = int(os.getenv("MAX_OUTPUT_TOKENS", "1500"))
            # Enable stateful Responses; reuse previous_response_id if available for this session
            prev_id = responses_prev_ids.get(session_id)
            
            # Prefer top-level instructions + string input per Responses docs
            kwargs = {
                "model": os.getenv("AI_MODEL", "gpt-5"),
                "instructions": system_prompt,
                "input": user_prompt_final,
                "reasoning": {"effort": eff},
                "max_output_tokens": min(1500, max_out),
                "store": True,
            }
            if prev_id:
                kwargs["previous_response_id"] = prev_id
                
            res = client.responses.create(**kwargs)
            reply = (extract_output_text(res) or "").strip()
            try:
                if getattr(res, 'id', None):
                    responses_prev_ids[session_id] = res.id  # store for next turn
            except Exception:
                pass
        except Exception as _e:
            logger.error(f"Responses API error: {_e}")
            return jsonify({"success": False, "error": f"Responses API error: {_e}"}), 500

        if not reply:
            return jsonify({"success": False, "error": "Réponse vide du modèle"}), 502

        # Persister dans la mémoire
        try:
            conversation_memory.add_message(session_id, 'user', user_message)
            conversation_memory.add_message(session_id, 'assistant', reply)
        except Exception:
            pass

        # Réponse rapide même en cas de réponses très longues
        try:
            clipped = reply[:3000] if isinstance(reply, str) and len(reply) > 3000 else reply
        except Exception:
            clipped = reply
        return jsonify({"success": True, "reply": clipped, "metadata": {"session_id": session_id}})
        
    except Exception as e:
        logger.error(f"Erreur markets_chat: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@markets_bp.route("/api/markets/chat/export-pdf", methods=["POST"])
def markets_chat_export_pdf():
    """Export serveur de la discussion chat au format PDF (Puppeteer, fallback WeasyPrint)."""
    try:
        data = request.get_json(silent=True) or {}
        # messages: [{ role: 'user'|'assistant', text: '...' }]
        messages = data.get('messages') or []
        if not isinstance(messages, list) or not messages:
            return jsonify({"success": False, "error": "Pas de contenu"}), 400

        # Construire HTML print-friendly
        def esc(s: str) -> str:
            return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        items_html = []
        for m in messages:
            role = m.get('role', 'assistant')
            txt = esc(m.get('text', ''))
            # Markdown gras minimal + emojis conservés
            txt = txt.replace('**', '<strong>').replace('<strong><strong>', '**')
            color = '#0ea5e9' if role == 'user' else '#a3e3f0'
            who = 'Vous' if role == 'user' else 'Assistant'
            items_html.append(f"""
              <div class='msg'><span class='who'>{who}:</span> <span class='txt'>{txt}</span></div>
            """)
            
        html_content = f"""
        <!doctype html>
        <html><head><meta charset='utf-8'>
        <style>
          @page {{ size: A4; margin: 16mm; }}
          body {{ font: 12pt 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial; color: #0f172a; }}
          h1 {{ font-size: 16pt; margin: 0 0 12pt; }}
          .meta {{ color:#64748b; font-size:10pt; margin-bottom:12pt; }}
          .msg {{ margin: 8pt 0; line-height: 1.5; word-break: break-word; }}
          .who {{ font-weight: 700; color:#0ea5e9; }}
          .txt strong {{ font-weight: 700; }}
        </style>
        </head>
        <body>
          <h1>Discussion Chatbot Marchés</h1>
          <div class='meta'>{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
          {''.join(items_html)}
        </body></html>
        """

        # Générer via Puppeteer si possible
        try:
            import tempfile, subprocess
            html_fd, html_path = tempfile.mkstemp(suffix='.html')
            with os.fdopen(html_fd, 'w', encoding='utf-8') as f:
                f.write(html_content)
            pdf_fd, pdf_path = tempfile.mkstemp(suffix='.pdf')
            os.close(pdf_fd)
            node_cmd = os.getenv('NODE_BIN', 'node')
            script_path = os.path.join(os.getcwd(), 'tools', 'puppeteer_print.js')
            cmd = [node_cmd, script_path, '--file', html_path, '--out', pdf_path, '--landscape', 'false', '--format', 'A4', '--margin', '16mm', '--wait-until', 'networkidle0']
            completed = subprocess.run(cmd, capture_output=True)
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.decode('utf-8', errors='ignore'))
            with open(pdf_path, 'rb') as fpdf:
                pdf_bytes = fpdf.read()
            os.remove(html_path); os.remove(pdf_path)
            return Response(pdf_bytes, mimetype='application/pdf', headers={'Content-Disposition': 'attachment; filename="chat_update_marches.pdf"'})
        except Exception as e:
            logger.error(f"Export PDF puppeteer échec: {e}")
            # Fallback WeasyPrint
            try:
                from weasyprint import HTML
                pdf_bytes = HTML(string=html_content).write_pdf()
                return Response(pdf_bytes, mimetype='application/pdf', headers={'Content-Disposition': 'attachment; filename="chat_update_marches.pdf"'})
            except Exception as e2:
                logger.error(f"Export PDF weasyprint échec: {e2}")
                return jsonify({"success": False, "error": "Export PDF échoué"}), 500
                
    except Exception as e:
        logger.error(f"Erreur markets_chat_export_pdf: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
