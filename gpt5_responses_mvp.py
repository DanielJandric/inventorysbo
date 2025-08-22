# gpt5_responses_mvp.py
import os, json, sys
from openai import OpenAI, OpenAIError

MODEL_PRIMARY = os.getenv("MODEL_PRIMARY", "gpt-5")                # alias stable d'abord
MODEL_SECOND  = os.getenv("MODEL_SECOND",  "gpt-5-2025-08-07")     # snapshot si besoin
MAX_OUT       = int(os.getenv("MAX_OUT", "384"))
TIMEOUT_S     = int(os.getenv("TIMEOUT_S", "60"))
FALLBACK_CHAT = os.getenv("FALLBACK_CHAT", "0") == "1"             # fallback chat optionnel

client = OpenAI()

INSTRUCTIONS = (
    "Tu es un analyste marchés. Texte brut, lisible, concis et actionnable. "
    "Reconnais tendances/corrélations/régimes de volatilité et commente risques/opportunités. "
    "N'invente aucun chiffre. Autorisé: **gras** et emojis sobres (↑, ↓, 🟢, 🔴, ⚠️, 💡). "
    "Structure 3–5 lignes numérotées, puis une conclusion. Pas de titres, pas de tableaux, pas de code."
)

def call_responses(prompt_text: str, model: str) -> tuple[str, dict]:
    """Retourne (texte, meta) — meta inclut request_id et usage."""
    res = client.responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=(
            prompt_text.strip()
            + "\n\nÉcris la RÉPONSE FINALE maintenant en texte brut, 3–5 lignes numérotées, puis une conclusion. "
              "Commence par: OK –"
        ),
        tool_choice="none",
        text={"format": {"type": "text"}, "verbosity": "medium"},
        max_output_tokens=MAX_OUT,
        timeout=TIMEOUT_S
        # ⚠️ ne PAS envoyer 'reasoning' -> évite d'absorber le budget en pensée
    )
    out = (res.output_text or "").strip()
    meta = {
        "request_id": getattr(res, "_request_id", None),
        "usage": getattr(res, "usage", None),
        "status": getattr(res, "status", None),
        "model": model,
    }
    return out, meta

def call_chat_fallback(prompt_text: str) -> str:
    """Fallback via Chat Completions (optionnel) pour garantir une sortie."""
    msgs = [
        {"role":"system","content":INSTRUCTIONS},
        {"role":"user","content":(
            prompt_text.strip()
            + "\n\nRéponds en texte brut uniquement. Commence par: OK –"
        )}
    ]
    resp = client.chat.completions.create(
        model="gpt-5-chat-latest",
        messages=msgs,
        max_tokens=min(MAX_OUT, 600),
        temperature=0.2
    )
    return (resp.choices[0].message.content or "").strip()

def run(prompt: str) -> int:
    # Tentative 1: alias stable
    text, meta = call_responses(prompt, MODEL_PRIMARY)
    print(f"[responses:{MODEL_PRIMARY}] request_id={meta['request_id']} usage={meta['usage']}")
    if text:
        print(text)
        return 0

    # Tentative 2: snapshot
    text, meta = call_responses(prompt, MODEL_SECOND)
    print(f"[responses:{MODEL_SECOND}] request_id={meta['request_id']} usage={meta['usage']}")
    if text:
        print(text)
        return 0

    # Fallback optionnel (désactivé par défaut)
    if FALLBACK_CHAT:
        print("[info] Responses vide -> fallback chat.gpt-5-chat-latest")
        text = call_chat_fallback(prompt)
        if text:
            print(text)
            return 0

    # Message UX sûr si tout échoue
    print("OK – Besoin de précisions : la sortie est vide avec Responses. Reformule la question en une phrase claire.")
    return 2

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Veuillez définir OPENAI_API_KEY.", file=sys.stderr)
        sys.exit(1)
    user_q = sys.argv[1] if len(sys.argv) > 1 else "Quelles opportunités sur l'immobilier coté aujourd'hui ?"
    try:
        sys.exit(run(user_q))
    except OpenAIError as e:
        print(f"[OpenAIError] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)
