"""Cold memory compression - compress old warm memories into summaries."""

import json
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session

from api.app.models.cold_memory import ColdMemory
from api.app.memory.warm import get_warm_memory
from api.app.llm import get_llm_client

logger = logging.getLogger(__name__)

WARM_FACTS_THRESHOLD = 50
WARM_MEMORIES_THRESHOLD = 30
CUTOFF_DAYS = 30

COMPRESSION_PROMPT = """Summarize these bot memories into a concise paragraph.
Preserve key facts, important relationships, and significant events.
Keep the summary under 500 words.

Facts:
{facts}

Memories:
{memories}

Relationships:
{relationships}

Return ONLY a summary paragraph, no JSON or formatting."""


def _is_old(item: dict, cutoff_days: int) -> bool:
    """Check if a memory item is older than cutoff."""
    item_date = item.get("date", "")
    if not item_date:
        return False
    try:
        cutoff = date.today() - timedelta(days=cutoff_days)
        return date.fromisoformat(item_date) < cutoff
    except (ValueError, TypeError):
        return False


def _get_oldest_date(items: list[dict]) -> date:
    """Get the oldest date from a list of items."""
    dates = []
    for item in items:
        try:
            dates.append(date.fromisoformat(item.get("date", "")))
        except (ValueError, TypeError):
            continue
    return min(dates) if dates else date.today()


async def maybe_compress_to_cold(db: Session, bot_id: str):
    """Check thresholds and compress if needed."""
    warm = get_warm_memory(db, bot_id)
    if warm is None:
        return

    facts_count = len(warm.facts_learned)
    memories_count = len(warm.memories)

    if facts_count > WARM_FACTS_THRESHOLD or memories_count > WARM_MEMORIES_THRESHOLD:
        logger.info(
            f"Compressing warm memory for {bot_id}: "
            f"{facts_count} facts, {memories_count} memories"
        )
        await compress_to_cold(db, bot_id)


async def compress_to_cold(db: Session, bot_id: str, cutoff_days: int = CUTOFF_DAYS):
    """Compress warm memories older than cutoff into cold summary."""
    warm = get_warm_memory(db, bot_id)
    if warm is None:
        return

    # Filter old items
    old_facts = [f for f in warm.facts_learned if _is_old(f, cutoff_days)]
    old_memories = [m for m in warm.memories if _is_old(m, cutoff_days)]

    if not old_facts and not old_memories:
        return  # Nothing to compress

    # Build prompt for summarization
    facts_text = "\n".join(f"- {f.get('fact', '')}" for f in old_facts) or "None"
    memories_text = "\n".join(f"- {m.get('summary', '')}" for m in old_memories) or "None"
    relationships_text = "\n".join(
        f"- {r.get('bot', '?')}: {r.get('sentiment', '?')}" for r in warm.relationships
    ) or "None"

    prompt = COMPRESSION_PROMPT.format(
        facts=facts_text,
        memories=memories_text,
        relationships=relationships_text,
    )

    # Summarize with Haiku
    llm = get_llm_client()
    try:
        response = await llm.think(
            prompt=prompt,
            model="claude-haiku-3-5-20241022",
            temperature=0.3,
            max_tokens=600,
        )
        summary = response.content.strip()
    except Exception as e:
        logger.warning(f"Cold compression LLM failed for {bot_id}: {e}")
        # Fallback: concatenate top facts
        summary = "Key facts: " + "; ".join(
            f.get("fact", "") for f in old_facts[:10]
        )

    # Save to cold storage
    cold = ColdMemory(
        bot_id=bot_id,
        period_start=_get_oldest_date(old_facts + old_memories),
        period_end=date.today(),
        summary=summary,
        key_relationships=[
            {"bot": r.get("bot"), "sentiment": r.get("sentiment")}
            for r in warm.relationships
        ],
        facts_compressed=len(old_facts),
        memories_compressed=len(old_memories),
    )
    db.add(cold)

    # Prune old items from warm memory
    warm.facts_learned = [f for f in warm.facts_learned if not _is_old(f, cutoff_days)]
    warm.memories = [m for m in warm.memories if not _is_old(m, cutoff_days)]
    db.commit()

    logger.info(
        f"Cold compression complete for {bot_id}: "
        f"compressed {len(old_facts)} facts + {len(old_memories)} memories"
    )
