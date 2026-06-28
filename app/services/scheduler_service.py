import logging
import os
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scrapers.orchestrator import main as run_scrapers
from app.services.outreach_engine import OutreachEngine

logger = logging.getLogger("SchedulerService")

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.enabled = os.environ.get("ENABLE_SCHEDULER", "false").lower() == "true"
        self.interval_minutes = int(os.environ.get("SCRAPER_INTERVAL", "60"))
        # Optional outreach draft generator
        self.enable_outreach_drafts = os.environ.get("ENABLE_OUTREACH_DRAFTS", "false").lower() == "true"
        self.outreach_interval_minutes = int(os.environ.get("OUTREACH_DRAFT_INTERVAL", "240"))
        self.outreach_output_dir = Path(os.environ.get("OUTREACH_DRAFT_DIR", "reports/outreach_drafts"))

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

        if self.enable_outreach_drafts:
            logger.info(
                "Outreach draft generator enabled (Interval: %sm, Dir: %s)",
                self.outreach_interval_minutes,
                str(self.outreach_output_dir),
            )
            self.scheduler.add_job(
                self._generate_outreach_draft,
                "interval",
                minutes=self.outreach_interval_minutes,
                id="outreach_draft",
                replace_existing=True,
            )

        self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down.")

    async def _generate_outreach_draft(self):
        try:
            self.outreach_output_dir.mkdir(parents=True, exist_ok=True)
            engine = OutreachEngine()
            # Minimal context draft
            content = await engine.generate_email(
                project_context="Upcoming accessibility and safety repairs for elderly homeowners in Lawton, OK.",
                call_to_action="Let us know what materials you can provide this month; we can arrange pickup or delivery.",
            )
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = self.outreach_output_dir / f"outreach_draft_{ts}.txt"
            out_path.write_text(content, encoding="utf-8")
            logger.info("Wrote outreach draft: %s", out_path)
        except Exception as e:
            logger.exception("Failed generating outreach draft: %s", e)
