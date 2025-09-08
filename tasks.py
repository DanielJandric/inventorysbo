import time
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
    for i, step in enumerate(steps, start=1):
        self.update_state(
            state="PROGRESS",
            meta={"step": step, "pct": int(i / len(steps) * 100)},
        )
        time.sleep(0.2)  # remplace par le vrai travail
        result["events"].append({"step": step, "ok": True})
    # TODO: brancher ici la logique existante de /api/chatbot
    return {"ok": True, "answer": "Réponse de démonstration", "meta": result}


@celery.task(bind=True, queue="pdf")
def pdf_task(self, payload: dict):
    """
    Tâche génération PDF (WeasyPrint) isolée du web.
    """
    # TODO: appeler le code existant qui génère le PDF et renvoyer un lien ou binaire stocké
    return {"ok": True, "pdf_url": "/downloads/report.pdf"}


