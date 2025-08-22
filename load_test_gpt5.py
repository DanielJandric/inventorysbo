# load_test_gpt5.py
import asyncio, time, statistics as stats, os, random
from typing import Dict, Any
from openai import AsyncOpenAI

N_REQUESTS = int(os.getenv("LT_REQS", "20"))        # total requêtes
CONCURRENCY = int(os.getenv("LT_CONC", "5"))        # parallélisme
TIMEOUT_S = int(os.getenv("LT_TIMEOUT", "60"))      # timeout par requête
MAX_TOKENS = int(os.getenv("LT_MAXTOK", "800"))     # tokens de sortie
EFFORT = os.getenv("LT_EFFORT", "medium")           # low|medium|high

PROMPTS = [
    "Dis: test marché OK.",
    "En une phrase: opportunités actions suisses ?",
    "Réponds en 1 ligne sans markdown: volatilité actuelle ?",
    "Rédige une phrase simple et directe sur l'immobilier coté.",
]

client = AsyncOpenAI()

async def one_call(i: int, sem: asyncio.Semaphore) -> Dict[str, Any]:
    prompt = random.choice(PROMPTS)
    t0 = time.perf_counter()
    ok, txt, err = False, "", None
    try:
        async with sem:
            res = await client.responses.create(
                model="gpt-5",
                input=[
                    {"role":"system","content":"Réponds en français, une seule phrase, texte brut."},
                    {"role":"user","content":prompt}
                ],
                reasoning={"effort": EFFORT},
                max_output_tokens=MAX_TOKENS,
                timeout=TIMEOUT_S
            )
        txt = (res.output_text or "").strip()
        ok = bool(txt)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    dt = (time.perf_counter() - t0) * 1000
    return {"i": i, "lat_ms": dt, "ok": ok, "len": len(txt), "err": err, "sample": txt[:140]}

def summarize(results):
    lats = [r["lat_ms"] for r in results]
    ok = [r for r in results if r["ok"]]
    ko = [r for r in results if not r["ok"]]
    empties = [r for r in ok if r["len"] == 0]
    p = lambda q: round(stats.quantiles(lats, n=100)[q-1], 1) if len(lats) >= 100 else None
    print("\n=== SUMMARY ===")
    print(f"Total: {len(results)} | OK: {len(ok)} | KO: {len(ko)} | Empty text: {len(empties)}")
    print(f"Latency ms -> min:{round(min(lats),1)} mean:{round(stats.mean(lats),1)} "
          f"p50:{round(stats.median(lats),1)} p95:{round(sorted(lats)[int(0.95*len(lats))-1],1)} "
          f"max:{round(max(lats),1)}")
    if ko:
        print("\nErrors (up to 5):")
        for r in ko[:5]:
            print(f"- #{r['i']} {round(r['lat_ms'],1)}ms :: {r['err']}")
    if ok:
        print("\nSamples (up to 5):")
        for r in ok[:5]:
            print(f"- #{r['i']} {round(r['lat_ms'],1)}ms [{r['len']} chars]: {r['sample']}")

async def main():
    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [one_call(i, sem) for i in range(N_REQUESTS)]
    results = await asyncio.gather(*tasks)
    summarize(results)

if __name__ == "__main__":
    # Prérequis: export OPENAI_API_KEY=sk-...
    asyncio.run(main())
