import os
import json
import time
import requests

from stock_api_manager import FredAPI

def main() -> None:
    api_key = os.environ.get("FRED_API_KEY")
    print("FRED_API_KEY set:", bool(api_key))
    if not api_key:
        print("Missing FRED_API_KEY in environment")
        return

    # Direct HTTP test (no decorator)
    base = 'https://api.stlouisfed.org/fred/series/observations'
    for sid in ['DGS10', 'CPIAUCSL', 'UNRATE']:
        params = {
            'series_id': sid,
            'api_key': api_key,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 5,
        }
        r = requests.get(base, params=params, timeout=20)
        print(f"HTTP {sid} status=", r.status_code)
        if r.status_code != 200:
            print("Body:", r.text[:400])
        else:
            data = r.json()
            obs = [o for o in (data.get('observations') or []) if o.get('value') not in (None, '.', '')]
            print(f"{sid} observations count=", len(obs))
            if obs:
                print(f"{sid} top=", obs[0])

    # Wrapper test (with internal rate limiter)
    fa = FredAPI()
    print("\nWrapper tests (rate-limited):")
    t0 = time.time()
    print('DGS10:', fa.get_latest_yield('DGS10'))
    print('elapsed:', round(time.time() - t0, 2), 's')
    t0 = time.time()
    print('CPIAUCSL:', fa.get_latest_value('CPIAUCSL'))
    print('elapsed:', round(time.time() - t0, 2), 's')
    t0 = time.time()
    print('UNRATE:', fa.get_latest_value('UNRATE'))
    print('elapsed:', round(time.time() - t0, 2), 's')

if __name__ == '__main__':
    main()


