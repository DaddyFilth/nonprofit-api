import subprocess
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scrapers.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ScraperOrchestrator")

# Configuration (Defaults to localhost if not set)
INGEST_API_BASE = os.environ.get("INGEST_API_BASE", "http://localhost:8000")
INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "testtoken")

SCRAPERS = [
    {"name": "Craigslist Free", "command": ["python3", "scrapers/scrape_sites.py"], "env": {"SITE": "craigslist_free"}},
    {"name": "Craigslist Robot", "command": ["python3", "scrapers/scrape_sites.py"], "env": {"SITE": "craigslist_robot"}},
    {"name": "Beta Electronics", "command": ["python3", "scrapers/scrape_beta_electronics.py"]},
    {"name": "Crawl Free Items", "command": ["python3", "scrapers/crawl_free_items.py"], "env": {"MAX_DEPTH": "1", "MAX_PAGES": "10"}},
]

def run_scraper(scraper):
    name = scraper["name"]
    cmd = scraper["command"]
    extra_env = scraper.get("env", {})

    # Merge environments
    env = os.environ.copy()
    env.update(extra_env)
    env["INGEST_API_BASE"] = INGEST_API_BASE
    env["INGEST_TOKEN"] = INGEST_TOKEN

    logger.info(f"Starting scraper: {name}")
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Successfully completed: {name}")
            if result.stdout:
                logger.debug(f"Output: {result.stdout.strip()}")
        else:
            logger.error(f"Failed: {name} with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr.strip()}")
    except Exception as e:
        logger.exception(f"Exception occurred while running {name}: {e}")

def main():
    logger.info("--- Scraper Automation Cycle Started ---")
    start_time = datetime.now()

    for scraper in SCRAPERS:
        run_scraper(scraper)

    duration = datetime.now() - start_time
    logger.info(f"--- Scraper Automation Cycle Finished (Duration: {duration}) ---")

if __name__ == "__main__":
    main()
