#!/usr/bin/env python3
import asyncio
from scrapingbee_scraper import get_scrapingbee_scraper


async def main():
    scraper = get_scrapingbee_scraper()
    scraper.initialize_sync()
    try:
        items = await scraper.search_and_scrape_deep(
            "Analyse marché globale aujourd'hui avec focus IA",
            per_site=12,
            max_age_hours=72,
            min_chars=25000,
        )
        total_chars = sum(len((i.content or "")) for i in items)
        print(f"Articles: {len(items)} | chars={total_chars}")
        for idx, it in enumerate(items[:10], 1):
            src = (it.metadata or {}).get("source", "unknown")
            print(f"{idx}. {it.title[:80]}... src={src} chars={len(it.content or '')}")
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())


