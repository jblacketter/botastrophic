"""Load bot configurations from YAML files."""

import logging
from pathlib import Path
import yaml
from sqlalchemy.orm import Session

from api.app.models.bot import Bot


logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.parent / "config" / "bots"


def load_bot_config(yaml_path: Path) -> dict:
    """Load a single bot config from YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("bot", config)


def load_all_bot_configs() -> list[dict]:
    """Load all bot configs from the config directory."""
    configs = []
    if not CONFIG_DIR.exists():
        logger.warning(f"Bot config directory not found: {CONFIG_DIR}")
        return configs

    for yaml_file in CONFIG_DIR.glob("*.yaml"):
        try:
            config = load_bot_config(yaml_file)
            configs.append(config)
            logger.info(f"Loaded bot config: {config.get('name', yaml_file.stem)}")
        except Exception as e:
            logger.error(f"Failed to load bot config {yaml_file}: {e}")

    return configs


def sync_bots_to_db(db: Session) -> list[Bot]:
    """Sync bot configs from YAML files to database."""
    configs = load_all_bot_configs()
    bots = []

    for config in configs:
        bot_id = config.get("id")
        if not bot_id:
            logger.warning(f"Bot config missing 'id': {config}")
            continue

        # Check if bot exists
        existing = db.query(Bot).filter(Bot.id == bot_id).first()

        if existing:
            if existing.source == "yaml":
                # Only overwrite YAML-managed bots
                existing.name = config.get("name", existing.name)
                existing.personality_config = config
                logger.info(f"Updated bot: {existing.name}")
            else:
                logger.info(f"Skipping custom bot: {existing.name}")
            bots.append(existing)
        else:
            # Create new bot from YAML
            bot = Bot(
                id=bot_id,
                name=config.get("name", bot_id),
                personality_config=config,
                source="yaml",
            )
            db.add(bot)
            bots.append(bot)
            logger.info(f"Created bot: {bot.name}")

    db.commit()
    return bots
