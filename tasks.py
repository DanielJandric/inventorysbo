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
    Tâche chatbot marchés: délègue au web (force_sync) pour générer la réponse.
    """
    steps = ["prepare_request", "call_web", "postprocess"]
    result = {"events": []}
    data = (payload or {}).copy()
    self.update_state(state="PROGRESS", meta={"step": steps[0], "pct": 20})
    msg = (data.get("message") or "").strip()
    if not msg:
        return {"ok": False, "error": "Message vide", "meta": result}
    result["events"].append({"step": steps[0], "ok": True})

    self.update_state(state="PROGRESS", meta={"step": steps[1], "pct": 70})
    try:
        base = os.getenv("API_BASE_URL") or os.getenv("APP_URL") or "https://inventorysbo.onrender.com"
        if not (base.startswith("http://") or base.startswith("https://")):
            base = "https://" + base
        url = base.rstrip("/") + "/api/markets/chat?force_sync=1"
        timeout_s = int(os.getenv("CHATBOT_API_TIMEOUT", "60"))
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout_s)
        if resp.status_code == 200:
            body = resp.json()
            reply = body.get("reply") or body.get("message") or ""
            result["events"].append({"step": steps[1], "ok": True})
            self.update_state(state="PROGRESS", meta={"step": steps[2], "pct": 100})
            result["events"].append({"step": steps[2], "ok": True})
            return {"ok": True, "reply": reply, "meta": result}
        else:
            return {"ok": False, "error": f"web returned {resp.status_code}: {resp.text}", "meta": result}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e), "meta": result}


