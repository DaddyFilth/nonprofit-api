import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")

# Point this at a real freebie aggregator
SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://www.heyitsfree.net/"
)

ELECTRONICS_KEYWORDS = [
    "headphone", "earbud", "speaker", "bluetooth", "smartwatch",
    "tablet", "laptop", "monitor", "camera", "tv", "projector",
    "gaming", "controller", "robot vacuum", "vacuum robot",
    "air purifier", "hepa filter", "air cleaner",
    "roomba", "irobot", "shark", "shark ai", "honeywell",
]

TESTER_KEYWORDS = [
    "beta", "product tester", "test & keep", "test and keep",
    "review unit", "sample program", "product testing", "campaign",
    "trial", "ambassador", "freebie",
]


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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

    # Target specific post containers for thefreebieguy.com
    container_selector = "article, .post, .ast-article-post"
    title_selector = "h2.entry-title a, .title a"
    desc_selector = ".entry-content p, .post-content p"

    for idx, block in enumerate(soup.select(container_selector)):
        title_el = block.select_one(title_selector)
        desc_el = block.select_one(desc_selector)

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        raw_url = title_el.get("href")

        if not raw_url or raw_url.startswith("#"):
            continue

        if raw_url.startswith("/"):
            raw_url = urljoin(source_url, raw_url)

        description = desc_el.get_text(strip=True) if desc_el else ""
        full_text = f"{title} {description}"

        if not looks_like_electronics_beta(full_text):
            continue

        posted_at = datetime.now(timezone.utc)
        post_id = raw_url
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
