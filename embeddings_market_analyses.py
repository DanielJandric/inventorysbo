import os, json, time
from typing import Any, Dict, List
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
SKIP_EXISTING = os.getenv("SKIP_EXISTING", "0").lower() in ("1","true","yes")
PREFER_COLUMN = os.getenv("PREFER_EMBED_COLUMN", "0").lower() in ("1","true","yes")

if not (SUPABASE_URL and SUPABASE_KEY and OPENAI_API_KEY):
    raise SystemExit("Missing SUPABASE_URL / SUPABASE_KEY / OPENAI_API_KEY")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
oc = OpenAI(api_key=OPENAI_API_KEY)

def _as_list(val):
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x) for x in val if str(x).strip()]
    if isinstance(val, str):
        try:
            j = json.loads(val)
            if isinstance(j, list):
                return [str(x) for x in j if str(x).strip()]
        except Exception:
            pass
        return [val]
    return [str(val)]

def _as_dict(val):
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            j = json.loads(val)
            if isinstance(j, dict):
                return j
        except Exception:
            pass
    return {}

def build_text(row: Dict[str, Any]) -> str:
    parts: List[str] = []
    parts.append(str(row.get("analysis_type") or ""))
    parts.append(str(row.get("summary") or ""))
    for k in ("executive_summary","key_points","insights","risks","opportunities"):
        parts.extend(_as_list(row.get(k)))
    sd = _as_dict(row.get("structured_data"))
    # take some nested fields if present
    for k in ("deep_analysis","market_pulse","actionable_summary"):
        v = sd.get(k)
        if v:
            parts.append(str(v))
    text = " \n".join([p for p in parts if str(p).strip()])
    return text or (row.get("summary") or "market analysis")

def fetch_page(offset: int, limit: int) -> List[Dict[str, Any]]:
    resp = sb.table("market_analyses").select("*").order("id", desc=False).range(offset, offset + limit - 1).execute()
    return resp.data or []

def main():
    offset = 0
    processed = 0
    created = 0
    while True:
        rows = fetch_page(offset, BATCH_SIZE)
        if not rows:
            break
        for row in rows:
            try:
                # check existing
                sd = _as_dict(row.get("structured_data"))
                has_structured_emb = isinstance(sd.get("embedding_1536"), list) and len(sd.get("embedding_1536")) > 1000
                has_column_emb = row.get("embedding") is not None
                if SKIP_EXISTING and (has_column_emb or has_structured_emb):
                    processed += 1
                    continue
                txt = build_text(row)
                emb = oc.embeddings.create(model=MODEL, input=txt).data[0].embedding
                did = False
                if PREFER_COLUMN:
                    try:
                        sb.table("market_analyses").update({"embedding": emb}).eq("id", row["id"]).execute()
                        did = True
                    except Exception:
                        did = False
                if not did:
                    # store inside structured_data JSON
                    sd["embedding_1536"] = emb
                    sb.table("market_analyses").update({"structured_data": sd}).eq("id", row["id"]).execute()
                created += 1
                processed += 1
            except Exception as e:
                time.sleep(0.5)
        offset += BATCH_SIZE
    print(f"DONE analyses processed={processed} created={created}")

if __name__ == "__main__":
    main()
