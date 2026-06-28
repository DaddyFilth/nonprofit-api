import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


API_BASE = os.environ.get("INGEST_API_BASE", "http://127.0.0.1:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "devtoken")

SITE = os.environ.get("SITE", "craigslist_free")


SITE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "craigslist_free": {
        "source": "craigslist_free",
        "default_url": "https://lawton.craigslist.org/d/free-stuff/search/zip",
        "container": "li.result-row, li.cl-search-result",
        "title": "a.result-title, a.cl-app-anchor",
        "link": "a.result-title, a.cl-app-anchor",
        "desc": "",
        "location": "span.result-hood",
        "time": "time.result-date",
        "category": "general",
    },
    "craigslist_robot": {
        "source": "craigslist_robot",
        "default_url": "https://lawton.craigslist.org/search/sss?query=robot+vacuum&max_price=0",
        "container": "li.result-row, li.cl-search-result",
        "title": "a.result-title, a.cl-app-anchor",
        "link": "a.result-title, a.cl-app-anchor",
        "desc": "",
        "location": "span.result-hood",
        "time": "time.result-date",
        "category": "electronics",
    },
    "freecycle_like": {
        "source": "freecycle_like",
        "default_url": "https://example-freecycle.org/group/lawton/listings",
        "container": ".listing, .post, article, li.result",
        "title": ".title, h2 a, h3 a",
        "link": "a",
        "desc": ".description, p, .body",
        "location": ".location, .town, .city",
        "time": "time[datetime]",
        "category": "general",
    },
    "samples_directory": {
        "source": "samples_directory",
        "default_url": "https://moneypantry.com/websites-to-get-free-stuff/",
        "container": "article, .offer, li.freebie, .free-item",
        "title": "h2, h3, .title, a",
        "link": "a",
        "desc": "p, .description, .excerpt",
        "location": "",
        "time": "",
        "category": "samples",
    },
}


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NonprofitScraper/0.1; +https://example.org)"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_items(site_key: str, html: str, source_url: str) -> List[Dict[str, Any]]:
    cfg = SITE_CONFIGS[site_key]
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict[str, Any]] = []

    container_sel = cfg["container"]
    title_sel = cfg["title"]
    link_sel = cfg["link"]
    desc_sel = cfg["desc"]
    loc_sel = cfg["location"]
    time_sel = cfg["time"]
    category = cfg["category"]
    source = cfg["source"]

    for idx, card in enumerate(soup.select(container_sel)):
        title_el = card.select_one(title_sel) if title_sel else None
        link_el = card.select_one(link_sel) if link_sel else None
        desc_el = card.select_one(desc_sel) if desc_sel else None
        loc_el = card.select_one(loc_sel) if loc_sel else None
        time_el = card.select_one(time_sel) if time_sel else None

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        raw_url: Optional[str] = (
            link_el.get("href") if link_el and link_el.has_attr("href") else None
        )
        if raw_url and raw_url.startswith("/"):
            raw_url = urljoin(source_url, raw_url)
        if raw_url and raw_url.startswith("#"):
            raw_url = None

        description = desc_el.get_text(strip=True) if desc_el else ""
        location = loc_el.get_text(strip=True).strip(" ()") if loc_el else None

        posted_at = datetime.now(timezone.utc)
        if time_el and time_el.has_attr("datetime"):
            posted_raw = time_el.get("datetime")
            try:
                parsed = dateparser.isoparse(posted_raw)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                posted_at = parsed
            except Exception:
                pass

        post_id = (
            card.get("data-pid")
            or card.get("data-id")
            or (raw_url or f"{site_key}-row-{idx}")
        )
        item_id = f"{source}::{post_id}"

        items.append(
            {
                "id": item_id,
                "source": source,
                "title": title,
                "description": description,
                "category": category,
                "location": {"city": location, "lat": None, "lon": None},
                "raw_url": raw_url,
                "posted_at": posted_at.isoformat(),
                "expires_at": None,
            }
        )

    return items


def post_items(items: List[Dict[str, Any]]) -> None:
    if not items:
        print("No items found for SITE =", SITE)
        return

    api_url = f"{API_BASE.rstrip('/')}/ingest-items"
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    resp = requests.post(api_url, json=items, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Posted {len(items)} items for SITE={SITE} to {api_url}")


def main() -> None:
    if SITE not in SITE_CONFIGS:
        raise SystemExit(f"Unknown SITE '{SITE}'. Known: {list(SITE_CONFIGS.keys())}")

    cfg = SITE_CONFIGS[SITE]
    source_url = os.environ.get("SOURCE_URL", cfg["default_url"])

    html = fetch_page(source_url)
    items = parse_items(SITE, html, source_url)
    post_items(items)


if __name__ == "__main__":
    main()
