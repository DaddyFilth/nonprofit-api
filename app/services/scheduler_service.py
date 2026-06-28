import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scrapers.orchestrator import main as run_scrapers

logger = logging.getLogger("SchedulerService")

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.enabled = os.environ.get("ENABLE_SCHEDULER", "false").lower() == "true"
        self.interval_minutes = int(os.environ.get("SCRAPER_INTERVAL", "60"))

    def start(self):
        if not self.enabled:
            logger.info("Scheduler is disabled. Set ENABLE_SCHEDULER=true to enable.")
            return

        logger.info(f"Starting scraper scheduler (Interval: {self.interval_minutes}m)")

        # Add the scraper orchestrator task
        self.scheduler.add_job(
            run_scrapers,
            "interval",
            minutes=self.interval_minutes,
            id="scraper_sync",
            replace_existing=True
        )

        self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down.")
