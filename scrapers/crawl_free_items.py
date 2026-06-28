import os
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")

START_URL = os.environ.get("START_URL", "https://lawton.craigslist.org/d/free-stuff/search/zip")
MAX_DEPTH = int(os.environ.get("MAX_DEPTH", "1"))
MAX_PAGES = int(os.environ.get("MAX_PAGES", "20"))
CRAWL_DELAY = float(os.environ.get("CRAWL_DELAY", "2.0"))  # seconds


FREE_KEYWORDS = ["free", "giveaway", "no cost", "freebie"]
HOUSEHOLD_KEYWORDS = [
    "sofa", "couch", "table", "chair", "bed", "mattress", "dresser", "lamp",
    "microwave", "fridge", "refrigerator", "washer", "dryer", "toaster",
    "kitchen", "household", "furniture",
]
ELECTRONICS_KEYWORDS = [
    "tv", "television", "monitor", "laptop", "tablet", "phone", "speaker",
    "bluetooth", "headphone", "earbud", "camera", "console", "gaming",
    "robot vacuum", "roomba", "shark", "honeywell", "air purifier",
]


def fetch_page(url: str) -> Optional[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NonprofitCrawler/0.1; +https://example.org)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            print(f"[skip] {url} status={resp.status_code}")
            return None
        return resp.text
    except Exception as exc:
        print(f"[error] fetching {url}: {exc}")
        return None


def classify_item(text: str) -> Optional[str]:
    t = text.lower()
    if not any(k in t for k in FREE_KEYWORDS):
        return None
    is_elec = any(k in t for k in ELECTRONICS_KEYWORDS)
    is_house = any(k in t for k in HOUSEHOLD_KEYWORDS)
    if is_elec and not is_house:
        return "electronics"
    if is_house and not is_elec:
        return "household"
    if is_elec and is_house:
        return "household_electronics"
    return None


def extract_items_from_page(url: str, html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, Any]] = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        if not text:
            continue

        category = classify_item(text)
        if not category:
            continue

        raw_url = urljoin(url, a["href"])
        # basic sanity: avoid mailto, javascript, etc.
        if not raw_url.startswith("http"):
            continue

        item_id = f"crawl::{raw_url}"
        items.append(
            {
                "id": item_id,
                "source": "crawler",
                "title": text,
                "description": "",
                "category": category,
                "location": {"city": None, "lat": None, "lon": None},
                "raw_url": raw_url,
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": None,
            }
        )

    return items


def post_items(items: List[Dict[str, Any]]) -> None:
    if not items:
        print("No candidate items found.")
        return

    api_url = f"{API_BASE.rstrip('/')}/ingest-items"
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    resp = requests.post(api_url, json=items, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"[ingest] Posted {len(items)} items to {api_url}")


def crawl(start_url: str, max_depth: int, max_pages: int) -> List[Dict[str, Any]]:
    parsed_start = urlparse(start_url)
    base_domain = parsed_start.netloc

    visited = set()
    queue = deque([(start_url, 0)])
    all_items: List[Dict[str, Any]] = []
    pages_crawled = 0

    while queue and pages_crawled < max_pages:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        print(f"[crawl] depth={depth} url={url}")
        html = fetch_page(url)
        if html is None:
            continue

        pages_crawled += 1
        items = extract_items_from_page(url, html)
        all_items.extend(items)

        if depth < max_depth:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                parsed = urlparse(link)
                if parsed.scheme not in ("http", "https"):
                    continue
                if parsed.netloc != base_domain:
                    continue
                if link not in visited:
                    queue.append((link, depth + 1))

        time.sleep(CRAWL_DELAY)

    return all_items


def main() -> None:
    print(f"[start] Crawling from {START_URL} depth={MAX_DEPTH} max_pages={MAX_PAGES}")
    items = crawl(START_URL, MAX_DEPTH, MAX_PAGES)
    print(f"[done] Found {len(items)} candidate items")
    post_items(items)


if __name__ == "__main__":
    main()
