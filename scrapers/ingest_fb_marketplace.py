import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")
INPUT_FILE = os.environ.get("FBM_INPUT_FILE", "fb_marketplace_free.json")


def load_fbm_items() -> List[Dict[str, Any]]:
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    items: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for row in raw:
        posted_at = row.get("posted_at")
        try:
            if posted_at:
                posted_dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            else:
                posted_dt = now
        except Exception:
            posted_dt = now

        item_id = row.get("id") or f"fbm::{row.get('url','unknown')}"

        items.append(
            {
                "id": item_id,
                "source": "facebook_marketplace",
                "title": row.get("title", "Untitled item"),
                "description": row.get("description", ""),
                "category": row.get("category", "general"),
                "location": {
                    "city": row.get("city"),
                    "lat": None,
                    "lon": None,
                },
                "raw_url": row.get("url"),
                "posted_at": posted_dt.isoformat(),
                "expires_at": None,
            }
        )

    return items


def post_items(items: List[Dict[str, Any]]) -> None:
    if not items:
        print("No Marketplace items to ingest.")
        return

    api_url = f"{API_BASE.rstrip('/')}/ingest-items"
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    resp = requests.post(api_url, json=items, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Posted {len(items)} Marketplace items to {api_url}")


def main() -> None:
    items = load_fbm_items()
    post_items(items)


if __name__ == "__main__":
    main()
