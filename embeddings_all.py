import os
import time
from typing import List, Dict, Any

from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
SKIP_EXISTING = os.getenv("SKIP_EXISTING", "1").lower() in ("1", "true", "yes")

if not (SUPABASE_URL and SUPABASE_KEY and OPENAI_API_KEY):
    raise SystemExit("Missing SUPABASE_URL / SUPABASE_KEY / OPENAI_API_KEY")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
oc = OpenAI(api_key=OPENAI_API_KEY)

def build_text(item: Dict[str, Any]) -> str:
    fields = [
        item.get("name") or "",
        item.get("category") or "",
        item.get("status") or "",
        item.get("description") or "",
    ]
    text = " | ".join([str(x).strip() for x in fields if str(x).strip()])
    return text or (item.get("name") or "item")

def fetch_page(offset: int, limit: int) -> List[Dict[str, Any]]:
    resp = sb.table("items").select("*").order("id", desc=False).range(offset, offset + limit - 1).execute()
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
                if SKIP_EXISTING and row.get("embedding"):
                    processed += 1
                    continue
                text = build_text(row)
                emb = oc.embeddings.create(model=MODEL, input=text).data[0].embedding
                sb.table("items").update({"embedding": emb}).eq("id", row["id"]).execute()
                created += 1
                processed += 1
            except Exception as e:
                time.sleep(1.0)
        offset += BATCH_SIZE
    print(f"DONE processed={processed} created={created}")

if __name__ == "__main__":
    main()
