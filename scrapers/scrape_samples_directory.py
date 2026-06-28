import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")

# Use HeyItsFree.net as a real-world source for free samples
SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://www.heyitsfree.net/"
)


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

    # Selectors for heyitsfree.net (WordPress based)
    container_selector = "article.post, .post"
    title_selector = "h2.entry-title a, .title a"
    desc_selector = ".entry-summary p, .entry-content p"
    time_selector = "time.entry-date"

    for idx, block in enumerate(soup.select(container_selector)):
        title_el = block.select_one(title_selector)
        desc_el = block.select_one(desc_selector)
        time_el = block.select_one(time_selector)

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        raw_url = title_el.get("href")

        if not raw_url or raw_url.startswith("#"):
            continue

        if raw_url.startswith("/"):
            raw_url = urljoin(SOURCE_URL, raw_url)

        description = desc_el.get_text(strip=True) if desc_el else ""

        posted_raw = time_el.get("datetime") if time_el and time_el.has_attr("datetime") else None
        try:
            posted_at = dateparser.isoparse(posted_raw) if posted_raw else datetime.now(timezone.utc)
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
        except Exception:
            posted_at = datetime.now(timezone.utc)

        post_id = raw_url
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
