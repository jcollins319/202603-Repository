import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.etl.ingestion import ingest_recent_filings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler():
    """Start the background scheduler for periodic ingestion."""
    scheduler.add_job(
        ingest_recent_filings,
        "interval",
        seconds=settings.polling_interval_seconds,
        id="form4_ingestion",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started. Polling every %d seconds.",
        settings.polling_interval_seconds,
    )


def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped.")
