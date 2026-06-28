import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")
SOURCE_URL = os.environ.get("SOURCE_URL", "https://www.freebies.com/")


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_items(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, Any]] = []

    # Selectors for freebies.com
    # Usually grid items with titles in h3 or similar
    container_selector = ".view-content .views-row, div.node-freebie, .item-list li"
    title_selector = "h2, h3, .title, a"
    link_selector = "a"

    for idx, block in enumerate(soup.select(container_selector)):
        title_el = block.select_one(title_selector)
        link_el = block.select_one(link_selector)

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        raw_url = link_el.get("href") if link_el and link_el.has_attr("href") else None

        if not raw_url or raw_url.startswith("#"):
            continue

        if raw_url.startswith("/"):
            raw_url = urljoin(SOURCE_URL, raw_url)

        now = datetime.now(timezone.utc)
        item_id = f"freebies_com::{raw_url or idx}"

        items.append(
            {
                "id": item_id,
                "source": "freebies_com",
                "title": title,
                "description": "",
                "category": "general",
                "location": {"city": None, "lat": None, "lon": None},
                "raw_url": raw_url,
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
    html = fetch_page(SOURCE_URL)
    items = parse_items(html)
    post_items(items)


if __name__ == "__main__":
    main()
