import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")

# Example placeholder: replace with an actual Freecycle/local free board URL
SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://example-freecycle.org/group/lawton/listings"
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

    # TODO: Adjust these selectors to match the actual group's HTML
    container_selector = ".listing, .post, article, li.result"
    title_selector = ".title, h2 a, h3 a"
    link_selector = "a"
    desc_selector = ".description, p, .body"
    location_selector = ".location, .town, .city"
    time_selector = "time[datetime]"

    for idx, card in enumerate(soup.select(container_selector)):
        title_el = card.select_one(title_selector)
        link_el = card.select_one(link_selector)
        desc_el = card.select_one(desc_selector)
        loc_el = card.select_one(location_selector)
        time_el = card.select_one(time_selector)

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        raw_url: Optional[str] = (
            link_el.get("href") if link_el and link_el.has_attr("href") else None
        )
        if raw_url and raw_url.startswith("/"):
            raw_url = urljoin(SOURCE_URL, raw_url)

        description = desc_el.get_text(strip=True) if desc_el else ""
        location = loc_el.get_text(strip=True) if loc_el else None

        posted_raw = time_el.get("datetime") if time_el and time_el.has_attr("datetime") else None
        try:
            posted_at = dateparser.isoparse(posted_raw) if posted_raw else datetime.now(timezone.utc)
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
        except Exception:
            posted_at = datetime.now(timezone.utc)

        post_id = card.get("data-id") or (raw_url or f"row-{idx}")
        item_id = f"freecycle::{post_id}"

        items.append(
            {
                "id": item_id,
                "source": "freecycle_like",
                "title": title,
                "description": description,
                "category": "general",
                "location": {"city": location, "lat": None, "lon": None},
                "raw_url": raw_url,
                "posted_at": posted_at.isoformat(),
                "expires_at": None,
            }
        )

    return items


def post_items(items: List[Dict[str, Any]]) -> None:
    if not items:
        print("No freecycle-style items found.")
        return

    api_url = f"{API_BASE.rstrip('/')}/ingest-items"
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    resp = requests.post(api_url, json=items, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Posted {len(items)} freecycle-style items to {api_url}")


def main() -> None:
    html = fetch_page(SOURCE_URL)
    items = parse_items(html)
    post_items(items)


if __name__ == "__main__":
    main()
