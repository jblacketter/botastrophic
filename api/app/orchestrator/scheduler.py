"""Heartbeat scheduler using APScheduler."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from api.app.config import get_settings
from api.app.database import SessionLocal
from api.app.models.bot import Bot
from api.app.orchestrator.heartbeat import heartbeat


logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# Track current pace (in seconds)
_current_pace: int = 14400  # Default: 4 hours


async def run_weekly_cold_compression():
    """Run cold memory compression for all bots (weekly backup job)."""
    from api.app.memory.cold import compress_to_cold

    logger.info("Running weekly cold memory compression for all bots")
    db = SessionLocal()
    try:
        bots = db.query(Bot).all()
        for bot in bots:
            try:
                await compress_to_cold(db, bot.id)
            except Exception as e:
                logger.error(f"Cold compression failed for bot {bot.id}: {e}")
    finally:
        db.close()


async def run_all_heartbeats():
    """Run heartbeat for all active bots."""
    logger.info("Running scheduled heartbeats for all bots")

    db = SessionLocal()
    try:
        bots = db.query(Bot).all()
        for bot in bots:
            try:
                await heartbeat(bot.id, db)
            except Exception as e:
                logger.error(f"Heartbeat failed for bot {bot.id}: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the heartbeat scheduler."""
    global _current_pace
    settings = get_settings()
    _current_pace = settings.heartbeat_interval

    # Add job to run heartbeats at configured interval
    scheduler.add_job(
        run_all_heartbeats,
        trigger=IntervalTrigger(seconds=_current_pace),
        id="heartbeat_all",
        name="Run heartbeats for all bots",
        replace_existing=True,
    )

    # Weekly cold memory compression (Sunday 3am)
    scheduler.add_job(
        run_weekly_cold_compression,
        trigger=CronTrigger(day_of_week="sun", hour=3),
        id="cold_compression_weekly",
        name="Weekly cold memory compression",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started. Heartbeats every {_current_pace} seconds "
        f"({_current_pace / 3600:.1f} hours)"
    )


def get_current_pace() -> int:
    """Get current pace in seconds."""
    return _current_pace


def update_pace(interval_seconds: int) -> None:
    """Update the heartbeat interval dynamically."""
    global _current_pace
    _current_pace = interval_seconds

    # Reschedule the job with new interval
    scheduler.reschedule_job(
        "heartbeat_all",
        trigger=IntervalTrigger(seconds=interval_seconds),
    )

    logger.info(
        f"Pace updated. Heartbeats every {interval_seconds} seconds "
        f"({interval_seconds / 3600:.1f} hours)"
    )


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")


async def trigger_heartbeat(bot_id: str) -> dict:
    """Manually trigger a heartbeat for a specific bot."""
    db = SessionLocal()
    try:
        result = await heartbeat(bot_id, db)
        return result
    finally:
        db.close()
