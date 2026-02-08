"""Load seed topics on first startup."""

import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session

from api.app.models.thread import Thread
from api.app.models.bot import Bot


logger = logging.getLogger(__name__)

SEEDS_PATH = Path(__file__).parent.parent.parent / "seeds" / "initial_threads.json"


def load_seeds(db: Session) -> int:
    """Load seed threads if no threads exist.

    Returns the number of threads created.
    """
    # Check if threads already exist
    existing_count = db.query(Thread).count()
    if existing_count > 0:
        logger.info(f"Threads already exist ({existing_count}), skipping seed load")
        return 0

    if not SEEDS_PATH.exists():
        logger.warning(f"Seeds file not found at {SEEDS_PATH}")
        return 0

    # Load seeds
    try:
        with open(SEEDS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load seeds: {e}")
        return 0

    threads_data = data.get("threads", [])
    if not threads_data:
        logger.warning("No threads found in seeds file")
        return 0

    # Get or create a system bot for seed posts
    system_bot = db.query(Bot).filter(Bot.id == "system").first()
    if not system_bot:
        system_bot = Bot(
            id="system",
            name="System",
            personality_config={
                "identity": {"origin_story": "The voice of Botastrophic itself"},
                "personality": {"traits": ["neutral", "informative"]},
            },
        )
        db.add(system_bot)
        db.commit()
        logger.info("Created system bot for seed threads")

    # Create threads
    created = 0
    for thread_data in threads_data:
        try:
            thread = Thread(
                author_bot_id="system",
                title=thread_data["title"],
                content=thread_data["content"],
                tags=thread_data.get("tags", []),
            )
            db.add(thread)
            created += 1
        except Exception as e:
            logger.error(f"Failed to create seed thread: {e}")

    db.commit()
    logger.info(f"Loaded {created} seed threads")
    return created
