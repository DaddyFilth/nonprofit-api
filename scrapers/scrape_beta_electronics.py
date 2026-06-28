import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")

# Point this at a freebie / product testing roundup page
SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://example-freebie-directory.com/product-testing-electronics"
)

ELECTRONICS_KEYWORDS = [
    # generic electronics
    "headphone", "earbud", "speaker", "bluetooth", "smartwatch",
    "tablet", "laptop", "monitor", "camera", "tv", "projector",
    "gaming", "controller", "robot vacuum", "vacuum robot",
    # air purifiers
    "air purifier", "hepa filter", "air cleaner",
    # brand names
    "roomba", "irobot", "shark", "shark ai", "honeywell",
]

TESTER_KEYWORDS = [
    "beta", "product tester", "test & keep", "test and keep",
    "review unit", "sample program", "product testing", "campaign",
    "trial", "ambassador",
]


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NonprofitScraper/0.1; +https://example.org)"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def looks_like_electronics_beta(text: str) -> bool:
    t = text.lower()
    if not any(k in t for k in ELECTRONICS_KEYWORDS):
        return False
    return any(k in t for k in TESTER_KEYWORDS)


def parse_items(html: str, source_url: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, Any]] = []

    container_selector = "article, .offer, li, .free-item, .campaign"
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
        raw_url = link_el.get("href") if link_el and link_el.has_attr("href") else None
        if raw_url and raw_url.startswith("#"):
            raw_url = None
        if raw_url and raw_url.startswith("/"):
            raw_url = urljoin(source_url, raw_url)

        description = desc_el.get_text(strip=True) if desc_el else ""
        full_text = f"{title} {description}"

        if not looks_like_electronics_beta(full_text):
            continue

        posted_at = datetime.now(timezone.utc)
        post_id = raw_url or f"beta-elec-row-{idx}"
        item_id = f"beta_electronics::{post_id}"

        items.append(
            {
                "id": item_id,
                "source": "beta_electronics",
                "title": title,
                "description": description,
                "category": "electronics_beta",
                "location": {"city": None, "lat": None, "lon": None},
                "raw_url": raw_url,
                "posted_at": posted_at.isoformat(),
                "expires_at": None,
            }
        )

    return items


def post_items(items: List[Dict[str, Any]]) -> None:
    if not items:
        print("No electronics beta-testing offers found.")
        return

    api_url = f"{API_BASE.rstrip('/')}/ingest-items"
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    resp = requests.post(api_url, json=items, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Posted {len(items)} electronics beta-testing offers to {api_url}")


def main() -> None:
    html = fetch_page(SOURCE_URL)
    items = parse_items(html, SOURCE_URL)
    post_items(items)


if __name__ == "__main__":
    main()
