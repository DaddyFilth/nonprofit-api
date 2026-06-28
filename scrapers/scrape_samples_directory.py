import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")

# Example placeholder: a free-samples roundup article / directory
# You can point this at sites like MoneyPantry, Dealhack, or similar lists.[web:192][web:198]
SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://example-freebies-directory.com/free-samples"
)


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NonprofitScraper/0.1; +https://example.org)"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_items(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, Any]] = []

    # TODO: adjust selectors to match your chosen directory:
    # many "freebie list" posts use <article>, <li>, or <div class="offer">
    container_selector = "article, .offer, li.freebie, .free-item"
    title_selector = "h2, h3, .title, a"
    link_selector = "a"
    desc_selector = "p, .description, .excerpt"

    for idx, block in enumerate(soup.select(container_selector)):
        title_el = block.select_one(title_selector)
        link_el = block.select_one(link_selector)
        desc_el = block.select_one(desc_selector)

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        raw_url: Optional[str] = (
            link_el.get("href") if link_el and link_el.has_attr("href") else None
        )
        if raw_url and raw_url.startswith("#"):
            raw_url = None
        if raw_url and raw_url.startswith("/"):
            raw_url = urljoin(SOURCE_URL, raw_url)

        description = desc_el.get_text(strip=True) if desc_el else ""

        posted_at = datetime.now(timezone.utc)

        post_id = raw_url or f"row-{idx}"
        item_id = f"samples_dir::{post_id}"

        items.append(
            {
                "id": item_id,
                "source": "samples_directory",
                "title": title,
                "description": description,
                "category": "samples",
                "location": {"city": None, "lat": None, "lon": None},
                "raw_url": raw_url,
                "posted_at": posted_at.isoformat(),
                "expires_at": None,
            }
        )

    return items


def post_items(items: List[Dict[str, Any]]) -> None:
    if not items:
        print("No sample/freebie offers found.")
        return

    api_url = f"{API_BASE.rstrip('/')}/ingest-items"
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    resp = requests.post(api_url, json=items, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Posted {len(items)} sample/freebie offers to {api_url}")


def main() -> None:
    html = fetch_page(SOURCE_URL)
    items = parse_items(html)
    post_items(items)


if __name__ == "__main__":
    main()
