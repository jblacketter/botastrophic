"""Warm memory CRUD operations."""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from api.app.models.warm_memory import WarmMemory


logger = logging.getLogger(__name__)


def get_warm_memory(db: Session, bot_id: str) -> WarmMemory | None:
    """Get warm memory for a bot."""
    return db.query(WarmMemory).filter(WarmMemory.bot_id == bot_id).first()


def get_or_create_warm_memory(db: Session, bot_id: str) -> WarmMemory:
    """Get or create warm memory for a bot."""
    memory = get_warm_memory(db, bot_id)
    if memory is None:
        memory = WarmMemory(
            bot_id=bot_id,
            facts_learned=[],
            relationships=[],
            interests=[],
            opinions=[],
            memories=[],
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        logger.info(f"Created warm memory for bot {bot_id}")
    return memory


def update_warm_memory(
    db: Session,
    bot_id: str,
    facts: list | None = None,
    relationships: list | None = None,
    interests: list | None = None,
    opinions: list | None = None,
    memories: list | None = None,
) -> WarmMemory:
    """Update warm memory for a bot, merging new data with existing."""
    memory = get_or_create_warm_memory(db, bot_id)

    if facts:
        # Add new facts, avoid duplicates by fact text
        existing_facts = {f.get("fact") for f in memory.facts_learned}
        new_facts = [f for f in facts if f.get("fact") not in existing_facts]
        memory.facts_learned = memory.facts_learned + new_facts
        # Keep only last 50 facts
        memory.facts_learned = memory.facts_learned[-50:]

    if relationships:
        # Update or add relationships by bot name, preserving history
        existing_by_bot = {r.get("bot"): r for r in memory.relationships}
        for rel in relationships:
            bot_name = rel.get("bot")
            if bot_name in existing_by_bot:
                existing = existing_by_bot[bot_name]
                # Preserve and extend history
                history = existing.get("history", [])
                new_history = rel.get("history", [])
                if new_history:
                    history = history + new_history
                    history = history[-20:]  # Keep last 20 history events
                # Preserve interaction count, update last_interaction
                interaction_count = existing.get("interaction_count", 0)
                rel_count = rel.get("interaction_count")
                if rel_count is not None:
                    interaction_count = rel_count
                # Merge: new data overwrites, but keep history and count
                merged = {**existing, **rel}
                merged["history"] = history
                merged["interaction_count"] = interaction_count
                merged["last_interaction"] = rel.get("last_interaction", existing.get("last_interaction"))
                existing_by_bot[bot_name] = merged
            else:
                # New relationship - initialize tracking fields
                rel.setdefault("history", [])
                rel.setdefault("interaction_count", 0)
                rel.setdefault("last_interaction", None)
                existing_by_bot[bot_name] = rel
        memory.relationships = list(existing_by_bot.values())

    if interests:
        # Merge interests, keep unique
        existing = set(memory.interests)
        memory.interests = list(existing | set(interests))[:20]  # Max 20 interests

    if opinions:
        # Update or add opinions by topic
        existing_by_topic = {o.get("topic"): o for o in memory.opinions}
        for op in opinions:
            existing_by_topic[op.get("topic")] = op
        memory.opinions = list(existing_by_topic.values())

    if memories:
        # Add new memories
        memory.memories = memory.memories + memories
        # Keep only last 30 memories
        memory.memories = memory.memories[-30:]

    memory.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(memory)

    logger.debug(f"Updated warm memory for bot {bot_id}")
    return memory


def record_interaction(db: Session, bot_id: str, other_bot_id: str, event: str | None = None):
    """Record an interaction between two bots, incrementing count and optionally adding history."""
    from datetime import datetime as dt

    memory = get_or_create_warm_memory(db, bot_id)
    date_str = dt.utcnow().strftime("%Y-%m-%d")

    existing_by_bot = {r.get("bot"): r for r in memory.relationships}
    if other_bot_id in existing_by_bot:
        rel = existing_by_bot[other_bot_id]
        rel["interaction_count"] = rel.get("interaction_count", 0) + 1
        rel["last_interaction"] = date_str
        if event:
            history = rel.get("history", [])
            history.append({"date": date_str, "event": event})
            rel["history"] = history[-20:]
    else:
        rel = {
            "bot": other_bot_id,
            "sentiment": "neutral",
            "notes": "",
            "history": [{"date": date_str, "event": event}] if event else [],
            "interaction_count": 1,
            "last_interaction": date_str,
        }
        existing_by_bot[other_bot_id] = rel

    memory.relationships = list(existing_by_bot.values())
    memory.updated_at = dt.utcnow()
    db.commit()


def format_warm_memory_for_prompt(memory: WarmMemory | None) -> str:
    """Format warm memory for inclusion in bot prompt."""
    if memory is None:
        return "{}"

    sections = []

    if memory.relationships:
        rel_lines = []
        for rel in memory.relationships[:5]:  # Top 5 relationships
            line = f"- {rel.get('bot')}: {rel.get('sentiment', 'unknown')} - {rel.get('notes', '')}"
            count = rel.get("interaction_count", 0)
            if count:
                line += f" ({count} interactions)"
            last = rel.get("last_interaction")
            if last:
                line += f" [last: {last}]"
            rel_lines.append(line)
        if rel_lines:
            sections.append("Relationships:\n" + "\n".join(rel_lines))

    if memory.facts_learned:
        fact_lines = [f"- {f.get('fact')}" for f in memory.facts_learned[-5:]]
        if fact_lines:
            sections.append("Recent facts learned:\n" + "\n".join(fact_lines))

    if memory.opinions:
        op_lines = []
        for op in memory.opinions[:3]:
            op_lines.append(f"- {op.get('topic')}: {op.get('stance')} (confidence: {op.get('confidence', 0.5)})")
        if op_lines:
            sections.append("Current opinions:\n" + "\n".join(op_lines))

    if memory.interests:
        sections.append(f"Current interests: {', '.join(memory.interests[:10])}")

    return "\n\n".join(sections) if sections else "{}"
