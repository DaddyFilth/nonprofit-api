import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")

# Craigslist search for robot vacuums, price <= 0 (adjust city as needed)
# Example: general for-sale search:
#   https://lawton.craigslist.org/search/sss?query=robot+vacuum&max_price=0
SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://lawton.craigslist.org/search/sss?query=robot+vacuum&max_price=0"
)

KEYWORDS = ["robot vacuum", "robovac", "roomba", "vacuum robot"]


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NonprofitScraper/0.1; +https://example.org)"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def matches_keywords(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in KEYWORDS)


def parse_items(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, Any]] = []

    # Craigslist listings (classic + newer UI)[web:177][web:185]
    listings = soup.select("li.result-row, li.cl-search-result")

    for idx, li in enumerate(listings):
        title_tag = li.select_one("a.result-title, a.cl-app-anchor")
        time_tag = li.select_one("time.result-date")
        hood_tag = li.select_one("span.result-hood")
        price_tag = li.select_one("span.result-price")

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        raw_url: Optional[str] = title_tag.get("href")
        if raw_url and raw_url.startswith("/"):
            raw_url = urljoin(SOURCE_URL, raw_url)

        hood = hood_tag.get_text(strip=True).strip(" ()") if hood_tag else None
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        full_text = f"{title} {price_text} {hood or ''}"

        # Filter to robot-vacuum-related posts only
        if not matches_keywords(full_text):
            continue

        posted_raw = time_tag.get("datetime") if time_tag and time_tag.has_attr("datetime") else None
        try:
            posted_at = dateparser.isoparse(posted_raw) if posted_raw else datetime.now(timezone.utc)
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
        except Exception:
            posted_at = datetime.now(timezone.utc)

        post_id = li.get("data-pid") or (raw_url or f"row-{idx}")
        item_id = f"craigslist_robot::{post_id}"

        items.append(
            {
                "id": item_id,
                "source": "craigslist_robot",
                "title": title,
                "description": f"{price_text} {hood or ''}".strip(),
                "category": "electronics",
                "location": {"city": hood, "lat": None, "lon": None},
                "raw_url": raw_url,
                "posted_at": posted_at.isoformat(),
                "expires_at": None,
            }
        )

    return items


def post_items(items: List[Dict[str, Any]]) -> None:
    if not items:
        print("No robot vacuums found.")
        return

    api_url = f"{API_BASE.rstrip('/')}/ingest-items"
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    resp = requests.post(api_url, json=items, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Posted {len(items)} robot vacuum items to {api_url}")


def main() -> None:
    html = fetch_page(SOURCE_URL)
    items = parse_items(html)
    post_items(items)


if __name__ == "__main__":
    main()
