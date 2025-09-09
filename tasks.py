import os
import time
import json
import re
import requests
from typing import Optional, Any, Dict, List
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

    # Petits utilitaires
    def _coerce_base(url: str) -> str:
        if not (url.startswith("http://") or url.startswith("https://")):
            return "https://" + url
        return url

    def _fetch_items(api_base_url: str, timeout_s: int = 20) -> List[Dict[str, Any]]:
        try:
            url = api_base_url.rstrip("/") + "/api/items"
            r = requests.get(url, timeout=timeout_s)
            if r.status_code == 200:
                j = r.json()
                return j if isinstance(j, list) else []
        except Exception:
            pass
        return []

    def _is_available(it: Dict[str, Any]) -> bool:
        try:
            st = (it.get("status") or "").strip().lower()
            return st not in ("sold", "vendu", "vendue")
        except Exception:
            return False

    def _item_value(it: Dict[str, Any]) -> float:
        try:
            return float(it.get("current_value") or 0) if _is_available(it) else 0.0
        except Exception:
            return 0.0

    def _compute_basic_answer_or_none(message: str, api_base_url: str, timeout_s: int = 20) -> Optional[str]:
        try:
            m = (message or "").lower()
            items = None
            # Combien de X ?
            if "combien" in m:
                cat_map = {
                    "voiture": "voitures", "voitures": "voitures",
                    "montre": "montres", "montres": "montres",
                    "avion": "avions", "avions": "avions",
                    "bateau": "bateaux", "bateaux": "bateaux",
                    "action": "actions", "actions": "actions",
                }
                cat_detected = None
                for k in cat_map.keys():
                    if k in m:
                        cat_detected = cat_map[k]
                        break
                if cat_detected:
                    if items is None:
                        items = _fetch_items(api_base_url, timeout_s)
                    total = [it for it in items if str(it.get("category", "")).strip().lower() == cat_detected]
                    available = [it for it in total if _is_available(it)]
                    if any(tok in m for tok in ("total", "toutes", "au total")):
                        sold = [it for it in total if not _is_available(it)]
                        return f"Tu as {len(total)} {cat_detected} au total, dont {len(sold)} vendues et {len(available)} disponibles."
                    return f"Tu as {len(available)} {cat_detected} disponibles (non vendues)."

            # Valeur nette
            if ("valeur" in m and "nette" in m) or "net worth" in m:
                if items is None:
                    items = _fetch_items(api_base_url, timeout_s)
                total_value = sum(_item_value(it) for it in items)
                return f"La valeur nette (hors vendus) est de {total_value:,.0f} CHF."

            # Vaisseau amiral (meilleur actif disponible)
            if "vaisseau amiral" in m or "flagship" in m:
                if items is None:
                    items = _fetch_items(api_base_url, timeout_s)
                best = None
                best_v = -1.0
                for it in items:
                    v = _item_value(it)
                    if v > best_v:
                        best_v = v
                        best = it
                if best:
                    name = best.get("name") or "Actif principal"
                    cat = best.get("category") or ""
                    return f"Ton vaisseau amiral est {name} ({cat}) à ~{best_v:,.0f} CHF."
        except Exception:
            pass
        return None

    # Étape 2-4: d'abord tenter des réponses déterministes légères, sinon déléguer au web en mode synchrone pour vraie réponse (force_sync)
    self.update_state(state="PROGRESS", meta={"step": steps[1], "pct": 40})
    try:
        base = _coerce_base(os.getenv("API_BASE_URL") or os.getenv("APP_URL") or "https://inventorysbo.onrender.com")

        # Fallback déterministe avant l'appel lourd
        fb = _compute_basic_answer_or_none(msg, base, timeout_s=20)
        if fb:
            self.update_state(state="PROGRESS", meta={"step": steps[2], "pct": 70})
            result["events"].append({"step": steps[1], "ok": True})
            result["events"].append({"step": steps[2], "ok": True})
            self.update_state(state="PROGRESS", meta={"step": steps[3], "pct": 90})
            result["events"].append({"step": steps[3], "ok": True})
            self.update_state(state="PROGRESS", meta={"step": steps[4], "pct": 100})
            result["events"].append({"step": steps[4], "ok": True})
            return {"ok": True, "answer": fb, "meta": result}

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
            # Si toujours vide, retenter une fois rapidement puis fallback déterministe
            if not reply:
                try:
                    time.sleep(0.4)
                    resp2 = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout_s)
                    if resp2.status_code == 200:
                        b2 = resp2.json()
                        reply = b2.get("reply") or b2.get("answer") or b2.get("message") or ""
                except Exception:
                    pass
            if not reply:
                fb2 = _compute_basic_answer_or_none(msg, base, timeout_s=20)
                if fb2:
                    reply = fb2
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


