"""Quick sanity checks for the enhanced chatbot API endpoints.

Usage (from repo root):
    python tools/test_chatbot_endpoints.py --base-url http://127.0.0.1:5000

Requires: requests (pip install requests)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

import requests


def _status(session: requests.Session, url: str) -> Dict[str, Any]:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"Invalid JSON from {url}: {response.text[:200]}") from exc


def _post(session: requests.Session, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = session.post(url, json=payload, timeout=30)
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"Invalid JSON from {url}: {response.text[:200]}") from exc


def run_checks(base_url: str) -> None:
    session = requests.Session()
    summary: List[str] = []

    # 0. Metrics endpoint (quick health)
    data = _status(session, f"{base_url}/api/chatbot/metrics")
    summary.append(f"/api/chatbot/metrics -> {data}")

    # 1. Chatbot message
    chat_payload = {
        "message": "Donne-moi un résumé rapide de la collection.",
        "session_id": "test-session",
        "history": [],
    }
    data = _post(session, f"{base_url}/api/chatbot", chat_payload)
    summary.append(f"/api/chatbot -> keys: {list(data.keys())}")

    # 2. Intent analysis
    data = _post(session, f"{base_url}/api/chatbot/analyze-intent", {"query": "analyse mes montres"})
    summary.append(f"/api/chatbot/analyze-intent -> success={data.get('success')}")

    # 3. Prediction (uses dummy item)
    dummy_item = {
        "name": "Test Asset",
        "category": "Voitures",
        "current_value": 100000,
    }
    data = _post(
        session,
        f"{base_url}/api/chatbot/predict-value",
        {"item": dummy_item, "months": 12},
    )
    summary.append(f"/api/chatbot/predict-value -> keys: {list((data.get('predictions') or {}).keys())}")

    # 4. Portfolio metrics (checks data aggregation path)
    data = _post(
        session,
        f"{base_url}/api/chatbot/portfolio-metrics",
        {"items": [dummy_item]},
    )
    summary.append(f"/api/chatbot/portfolio-metrics -> success={data.get('success')}")

    print("\n".join(summary))


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ping chatbot endpoints")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:5000",
        help="Base URL of the Flask app (default: http://127.0.0.1:5000)",
    )
    args = parser.parse_args(argv)

    try:
        run_checks(args.base_url.rstrip("/"))
    except Exception as exc:  # pragma: no cover - debugging output for CLI
        print(f"❌ Check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

