import os
import time
import json
import re
import uuid
import requests
from typing import Optional, Any, Dict, List
from gpt5_compat import from_responses_simple, extract_output_text
from celery_app import celery
@celery.task(bind=True)
def chat_v2_task(self, payload: dict):
    """
    V2: Réponse rapide avec chemins déterministes; fallback court vers web v2 (force_sync).
    """
    steps = ["validate", "maybe_fast", "web_call", "finish"]
    self.update_state(state="PROGRESS", meta={"step": steps[0], "pct": 10})
    data = payload or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return {"ok": False, "error": "Message requis"}

    def _coerce_base(url: str) -> str:
        if not (url.startswith("http://") or url.startswith("https://")):
            return "https://" + url
        return url

    def _fast_or_none(message: str, api_base_url: str) -> str | None:
        try:
            return _compute_basic_answer_or_none(message, api_base_url, timeout_s=8)
        except Exception:
            return None

    def _direct_ai_or_none(message: str) -> Optional[str]:
        try:
            from openai import OpenAI  # lazy import
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None
            timeout_s = int(os.getenv("TIMEOUT_S", "45"))
            model = os.getenv("AI_MODEL", "gpt-5")
            client = OpenAI(api_key=api_key, timeout=timeout_s)
            # Contexte minimal: récupère un aperçu des items via l'API web (évite dépendance directe à Supabase ici)
            compact_ctx = ""
            try:
                url_items = base.rstrip("/") + "/api/items"
                r_items = requests.get(url_items, timeout=min(12, timeout_s))
                if r_items.status_code == 200:
                    data_items = r_items.json()
                    if isinstance(data_items, list):
                        # Catégories & top valeurs (disponibles)
                        def _is_av(it: Dict[str, Any]) -> bool:
                            st = str(it.get("status", "")).strip().lower()
                            return st not in ("sold", "vendu", "vendue")
                        def _val(it: Dict[str, Any]) -> float:
                            try:
                                if str(it.get("category", "")) == 'Actions' and it.get("current_price") and it.get("stock_quantity"):
                                    return float(it["current_price"]) * float(it["stock_quantity"]) if _is_av(it) else 0.0
                                return float(it.get("current_value") or 0) if _is_av(it) else 0.0
                            except Exception:
                                return 0.0
                        cats: Dict[str, int] = {}
                        for it in data_items:
                            c = str(it.get("category", "")).strip() or "Autres"
                            cats[c] = cats.get(c, 0) + 1
                        top = sorted(data_items, key=_val, reverse=True)[:5]
                        top_lines = []
                        for it in top:
                            v = _val(it)
                            if v <= 0:
                                continue
                            top_lines.append(f"- {it.get('name','?')} ({it.get('category','?')}) ~{int(v):,} CHF".replace(',', ' '))
                        cats_line = ", ".join([f"{k}:{v}" for k,v in cats.items()])
                        compact_ctx = (
                            f"Contexte Collection: catégories= [{cats_line}]\n"
                            f"Top par valeur:\n" + ("\n".join(top_lines) or "(n/a)")
                        )
            except Exception:
                compact_ctx = ""

            prompt = (
                "Tu es l'assistant BONVIN. Réponds en français, concis, structuré. "
                "Si tu n'as pas assez de contexte, propose une clarification en 1 phrase.\n\n"
                + (f"{compact_ctx}\n\n" if compact_ctx else "")
                + f"Question: {message}"
            )
            resp = from_responses_simple(
                client=client,
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            text = (extract_output_text(resp) or "").strip()
            return text or None
        except Exception:
            return None

    base = _coerce_base(os.getenv("API_BASE_URL") or os.getenv("APP_URL") or "https://inventorysbo.onrender.com")
    fb = _fast_or_none(msg, base)
    if fb:
        self.update_state(state="PROGRESS", meta={"step": steps[1], "pct": 60})
        self.update_state(state="PROGRESS", meta={"step": steps[3], "pct": 100})
        return {"ok": True, "answer": fb}

    # Fallback court via web v2
    self.update_state(state="PROGRESS", meta={"step": steps[2], "pct": 80})
    try:
        url = base.rstrip("/") + "/api/chatbot?force_sync=1"
        # Timeout plus large sur worker pour questions complexes
        timeout_s = int(os.getenv("CHATBOT_API_TIMEOUT", "45"))
        r = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data), timeout=timeout_s)
        if r.status_code == 200:
            body = r.json()
            reply = body.get("reply") or body.get("answer") or ""
            if not reply:
                reply = body.get("message") or ""
        else:
            reply = ""
        if not reply:
            # Dernier filet de sécurité
            reply = _fast_or_none(msg, base) or _direct_ai_or_none(msg) or "Réessayez dans un instant."
        self.update_state(state="PROGRESS", meta={"step": steps[3], "pct": 100})
        return {"ok": True, "answer": reply}
    except requests.exceptions.RequestException as e:
        # Ne jamais planter: tenter IA directe, sinon réponse courte
        fb_msg = _fast_or_none(msg, base) or _direct_ai_or_none(msg) or "Réponse indisponible pour l'instant. Réessayez dans un instant."
        return {"ok": True, "answer": fb_msg, "warning": str(e)}


@celery.task(bind=True)
def markets_chat_v2_task(self, payload: dict):
    """
    V2 marchés: délègue au web v2 (force_sync) avec budget court.
    """
    data = (payload or {}).copy()
    msg = (data.get("message") or "").strip()
    if not msg:
        return {"ok": False, "error": "Message vide"}
    def _coerce_base(url: str) -> str:
        if not (url.startswith("http://") or url.startswith("https://")):
            return "https://" + url
        return url
    try:
        base = _coerce_base(os.getenv("API_BASE_URL") or os.getenv("APP_URL") or "https://inventorysbo.onrender.com")
        url = base.rstrip("/") + "/api/markets/chat?force_sync=1"
        timeout_s = int(os.getenv("CHATBOT_API_TIMEOUT", "45"))
        r = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data), timeout=timeout_s)
        if r.status_code == 200:
            body = r.json()
            reply = body.get("reply") or body.get("message") or ""
            return {"ok": True, "reply": reply}
        # Fallback IA directe marchés (réponse courte)
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                client = OpenAI(api_key=api_key, timeout=int(os.getenv("TIMEOUT_S", "45")))
                model = os.getenv("AI_MODEL", "gpt-5")
                prompt = f"Question marchés: {msg}. Réponds brièvement (<=6 lignes)."
                resp = from_responses_simple(client=client, model=model, messages=[{"role":"user","content": prompt}])
                text = (extract_output_text(resp) or "").strip()
                if text:
                    return {"ok": True, "reply": text, "note": "direct_ai_fallback"}
            except Exception:
                pass
        return {"ok": False, "error": f"web returned {r.status_code}: {r.text}"}
    except requests.exceptions.RequestException as e:
        # Last resort
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                client = OpenAI(api_key=api_key, timeout=int(os.getenv("TIMEOUT_S", "45")))
                model = os.getenv("AI_MODEL", "gpt-5")
                prompt = f"Question marchés: {msg}. Réponds brièvement (<=6 lignes)."
                resp = from_responses_simple(client=client, model=model, messages=[{"role":"user","content": prompt}])
                text = (extract_output_text(resp) or "").strip()
                if text:
                    return {"ok": True, "reply": text, "warning": str(e), "note": "direct_ai_fallback"}
            except Exception:
                pass
        return {"ok": False, "error": str(e)}


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
    data = payload or {}
    session_id = data.get("session_id") or str(uuid.uuid4())
    history = data.get("history") or []
    # Étape 1: validation input
    self.update_state(state="PROGRESS", meta={"step": steps[0], "pct": 20})
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
                # Si le message cible les bateaux/navires/yachts, restreindre à la catégorie Bateaux
                boat_tokens = ("bateau", "bateaux", "navire", "navires", "yacht", "sunseeker", "axopar", "feadship")
                focus_boats = any(tok in m for tok in boat_tokens)
                pool = items
                if focus_boats:
                    pool = [it for it in items if str(it.get("category", "")).strip().lower() == "bateaux"]
                best = None
                best_v = -1.0
                for it in pool:
                    v = _item_value(it)
                    if v > best_v:
                        best_v = v
                        best = it
                if best:
                    name = best.get("name") or "Actif principal"
                    cat = best.get("category") or ""
                    if focus_boats:
                        return f"Ton vaisseau amiral (bateaux) est {name} ({cat}) à ~{best_v:,.0f} CHF."
                    return f"Ton vaisseau amiral est {name} ({cat}) à ~{best_v:,.0f} CHF."
        except Exception:
            pass
        return None

    # Étape 2-4: d'abord tenter des réponses déterministes légères, sinon exécuter le moteur LLM
    self.update_state(state="PROGRESS", meta={"step": steps[1], "pct": 40})
    base = _coerce_base(os.getenv("API_BASE_URL") or os.getenv("APP_URL") or "https://inventorysbo.onrender.com")

    fb = _compute_basic_answer_or_none(msg, base, timeout_s=10)
    if fb:
        self.update_state(state="PROGRESS", meta={"step": steps[2], "pct": 70})
        result["events"].extend([
            {"step": steps[1], "ok": True},
            {"step": steps[2], "ok": True},
        ])
        self.update_state(state="PROGRESS", meta={"step": steps[3], "pct": 90})
        result["events"].append({"step": steps[3], "ok": True})
        self.update_state(state="PROGRESS", meta={"step": steps[4], "pct": 100})
        result["events"].append({"step": steps[4], "ok": True})
        return {"ok": True, "answer": fb, "meta": result}

    # Déléguer au web en mode synchrone (force_sync=1) pour éviter imports complexes
    self.update_state(state="PROGRESS", meta={"step": steps[2], "pct": 55})
    try:
        url = base.rstrip("/") + "/api/chatbot?force_sync=1"
        timeout_s = int(os.getenv("CHATBOT_API_TIMEOUT", "60"))
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout_s)
        self.update_state(state="PROGRESS", meta={"step": steps[2], "pct": 70})
        if resp.status_code == 200:
            body = resp.json()
            reply = body.get("reply") or body.get("answer") or body.get("message") or ""
            if not reply:
                # Retry once
                time.sleep(0.5)
                resp2 = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout_s)
                if resp2.status_code == 200:
                    body2 = resp2.json()
                    reply = body2.get("reply") or body2.get("answer") or body2.get("message") or ""
            result["events"].extend([
                {"step": steps[1], "ok": True},
                {"step": steps[2], "ok": True},
                {"step": steps[3], "ok": True},
                {"step": steps[4], "ok": True},
            ])
            self.update_state(state="PROGRESS", meta={"step": steps[4], "pct": 100})
            return {"ok": True, "answer": reply, "meta": result}
        else:
            return {"ok": False, "error": f"web returned {resp.status_code}: {resp.text}", "meta": result}
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


