import os, json, time
from typing import Any, Dict, List
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
FORCE = os.getenv("FORCE", "1").lower() in ("1","true","yes")

if not (URL and KEY and OPENAI_API_KEY):
    raise SystemExit("Missing SUPABASE_URL / SUPABASE_KEY / OPENAI_API_KEY")

sb = create_client(URL, KEY)
oc = OpenAI(api_key=OPENAI_API_KEY)

def _as_dict(val):
    if val is None: return {}
    if isinstance(val, dict): return val
    if isinstance(val, str):
        try:
            j = json.loads(val)
            if isinstance(j, dict): return j
        except Exception:
            pass
    return {}

def _candidate_from_structured(row: Dict[str, Any]):
    sd = _as_dict(row.get("structured_data"))
    cand = sd.get("embedding_1536")
    if isinstance(cand, list) and len(cand) >= 512:
        try:
            return [float(x) for x in cand]
        except Exception:
            return None
    return None

def _build_text(row: Dict[str, Any]) -> str:
    parts: List[str] = []
    for k in ("analysis_type","summary"):
        v = row.get(k)
        if v: parts.append(str(v))
    sd = _as_dict(row.get("structured_data"))
    for k in ("executive_summary","key_points","insights","risks","opportunities"):
        v = row.get(k) or sd.get(k)
        if isinstance(v, list):
            parts.extend([str(x) for x in v if str(x).strip()])
    return " \n".join([p for p in parts if p]) or (row.get("summary") or "market analysis")

def _compute_embedding(text: str) -> List[float]:
    return oc.embeddings.create(model=MODEL, input=text).data[0].embedding

def fetch_page(offset: int, limit: int):
    resp = sb.table("market_analyses").select("*").order("id", desc=False).range(offset, offset + limit - 1).execute()
    return resp.data or []

def main():
    offset = 0
    processed = 0
    updated = 0
    while True:
        rows = fetch_page(offset, BATCH_SIZE)
        if not rows: break
        for row in rows:
            try:
                if (not FORCE) and row.get("embedding") is not None:
                    processed += 1
                    continue
                emb = _candidate_from_structured(row)
                if emb is None:
                    emb = _compute_embedding(_build_text(row))
                sb.table("market_analyses").update({"embedding": emb}).eq("id", row["id"]).execute()
                updated += 1
                processed += 1
            except Exception:
                time.sleep(0.5)
        offset += BATCH_SIZE
    print(f"DONE filled_column updated={updated} processed={processed}")

if __name__ == "__main__":
    main()
