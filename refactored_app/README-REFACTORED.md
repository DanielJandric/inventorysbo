# Refactored App (Parallel Test Build)

This folder contains a minimal, modular Flask app to validate a cleaner structure without touching the current monolith.

## Run (local)
- Ensure env: set `OPENAI_API_KEY` (optional), `AI_MODEL` (e.g., `gpt-4o-mini`), and database env (`SUPABASE_URL`, `SUPABASE_KEY`) if you want live items.
- Start: `python -m refactored_app.run`
- App serves on `http://127.0.0.1:5050`.

## Endpoints
- `POST /api/chatbot` {"message": "..."}
- `POST /api/markets/chat` {"message": "..."}
- `GET /api/metrics` → basic status (OpenAI connected, model, flags)

## Notes
- Items are fetched from Supabase if configured, else fallback to `API_BASE_URL/api/items`.
- Quick answers work without OpenAI when `ALWAYS_LLM=0` (default here).
- AI responses use OpenAI Responses or Chat Completions via a small engine wrapper.

