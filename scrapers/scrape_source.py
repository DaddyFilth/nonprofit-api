import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")
SOURCE_URL = os.environ.get("SOURCE_URL", "https://example.com")


def fetch_page(url: str) -> str:
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_items(html: str) -> List[Dict[str, Any]]:
    # placeholder parser: swap this for real selectors once pipeline is proven
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, Any]] = []

    now = datetime.now(timezone.utc)
    items.append(
        {
            "id": f"scraper::test::{int(now.timestamp())}",
            "source": "example",
            "title": "Scraper Test Item",
            "description": "Created by scrape_source.py",
            "category": "general",
            "location": {"city": "Lawton", "lat": None, "lon": None},
            "raw_url": SOURCE_URL,
            "posted_at": now.isoformat(),
            "expires_at": None,
        }
    )
    return items


def post_items(items: List[Dict[str, Any]]) -> None:
    if not items:
        print("No items to post.")
        return

    api_url = f"{API_BASE.rstrip('/')}/ingest-items"
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    resp = requests.post(api_url, json=items, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Posted {len(items)} items to {api_url}")


def main() -> None:
    # For now, generate a fake HTML and a test item
    # Later, you'll use: html = fetch_page(SOURCE_URL)
    html = fetch_page(SOURCE_URL)
    items = parse_items(html)
    post_items(items)


if __name__ == "__main__":
    main()
