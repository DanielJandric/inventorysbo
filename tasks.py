import os
import time
import json
import requests
from celery_app import celery


@celery.task(bind=True)
def chat_task(self, payload: dict):
    """
    Tâche LLM longue: orchestrer RAG + appel modèle + post-traitement.
    Publie l'avancement via self.update_state(meta=...).
    """
    steps = [
        "validation_input",
        "fetch_context",
        "llm_call",
        "postprocess",
        "format_output",
    ]
    result = {"events": []}
    # Étape 1: validation input
    self.update_state(state="PROGRESS", meta={"step": steps[0], "pct": 20})
    data = payload or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return {"ok": False, "error": "Message requis", "meta": result}
    result["events"].append({"step": steps[0], "ok": True})

    # Étape 2-4: déléguer au web en mode synchrone pour vraie réponse (force_sync)
    self.update_state(state="PROGRESS", meta={"step": steps[1], "pct": 40})
    try:
        base = os.getenv("API_BASE_URL") or os.getenv("APP_URL") or "https://inventorysbo.onrender.com"
        if not (base.startswith("http://") or base.startswith("https://")):
            base = "https://" + base
        url = base.rstrip("/") + "/api/chatbot?force_sync=1"
        # Respecter un timeout raisonnable
        timeout_s = int(os.getenv("CHATBOT_API_TIMEOUT", "60"))
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout_s)
        self.update_state(state="PROGRESS", meta={"step": steps[2], "pct": 70})
        if resp.status_code == 200:
            body = resp.json()
            reply = body.get("reply") or body.get("answer") or ""
            if not reply:
                reply = body.get("message") or ""
            result["events"].append({"step": steps[1], "ok": True})
            result["events"].append({"step": steps[2], "ok": True})
            self.update_state(state="PROGRESS", meta={"step": steps[3], "pct": 90})
            result["events"].append({"step": steps[3], "ok": True})
            self.update_state(state="PROGRESS", meta={"step": steps[4], "pct": 100})
            result["events"].append({"step": steps[4], "ok": True})
            return {"ok": True, "answer": reply, "meta": result}
        else:
            err = resp.text
            return {"ok": False, "error": f"web returned {resp.status_code}: {err}", "meta": result}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e), "meta": result}


@celery.task(bind=True, queue="pdf")
def pdf_task(self, payload: dict):
    """
    Tâche génération PDF (WeasyPrint) isolée du web.
    """
    # TODO: appeler le code existant qui génère le PDF et renvoyer un lien ou binaire stocké
    return {"ok": True, "pdf_url": "/downloads/report.pdf"}


@celery.task(bind=True)
def markets_chat_task(self, payload: dict):
    """
    Tâche chatbot marchés: assemble le contexte et génère une réponse via le worker marchés.
    """
    data = payload or {}
    user_message = (data.get("message") or "").strip()
    extra_context = (data.get("context") or "").strip()
    session_id = (data.get("session_id") or "").strip()

    steps = ["prepare_context", "llm_call", "postprocess"]
    result = {"events": []}

    # Étape 1: contexte (dernier rapport marchés)
    self.update_state(state="PROGRESS", meta={"step": steps[0], "pct": 20})
    try:
        from market_analysis_db import get_market_analysis_db
        db = get_market_analysis_db()
        latest = db.get_recent_analyses(limit=1)
        if latest:
            a = latest[0]
            exec_summary = "\n".join([f"- {p}" for p in (a.executive_summary or [])]) if getattr(a, 'executive_summary', None) else ""
            summary_compact = (a.summary or "")[:800]
            ts = a.timestamp or a.created_at or ""
            latest_txt = (
                f"[Dernier rapport | {a.analysis_type or 'auto'} | {ts}]\n"
                f"Executive Summary:\n{exec_summary}\n"
                f"Résumé:\n{summary_compact}"
            )
            extra_context = (extra_context + "\n---\n" + latest_txt).strip() if extra_context else latest_txt
    except Exception:
        pass
    result["events"].append({"step": steps[0], "ok": True})

    # Étape 2: appel LLM via worker marchés
    self.update_state(state="PROGRESS", meta={"step": steps[1], "pct": 70})
    reply_text = ""
    try:
        from markets_chat_worker import get_markets_chat_worker
        worker = get_markets_chat_worker()
        reply_text = worker.generate_reply(user_message, extra_context, history=[])
    except Exception as e:
        return {"ok": False, "error": str(e), "meta": result}
    result["events"].append({"step": steps[1], "ok": True})

    # Étape 3: post-traitement léger
    self.update_state(state="PROGRESS", meta={"step": steps[2], "pct": 100})
    result["events"].append({"step": steps[2], "ok": True})

    return {"ok": True, "reply": reply_text, "meta": result, "session_id": session_id}


