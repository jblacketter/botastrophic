"""Memory filtering for context injection."""

import re
import logging
from api.app.models.warm_memory import WarmMemory


logger = logging.getLogger(__name__)


def extract_keywords(text: str) -> set[str]:
    """Extract keywords from text for matching."""
    # Simple keyword extraction: lowercase words, filter short ones
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    # Remove common stop words
    stop_words = {
        'this', 'that', 'with', 'from', 'they', 'been', 'have', 'were',
        'being', 'their', 'there', 'what', 'when', 'where', 'which',
        'would', 'could', 'should', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'just', 'only', 'other', 'some',
        'such', 'more', 'most', 'very', 'also', 'really', 'think', 'like',
    }
    return set(words) - stop_words


def filter_relevant_memories(memory: WarmMemory | None, feed_text: str, max_items: int = 5) -> dict:
    """Filter warm memory for items relevant to current feed topics.

    Uses simple keyword matching (Phase 2). Embedding-based matching deferred to Phase 3.
    """
    if memory is None:
        return {
            "facts": [],
            "relationships": [],
            "opinions": [],
            "interests": [],
        }

    feed_keywords = extract_keywords(feed_text)

    # Score and filter facts
    scored_facts = []
    for fact in memory.facts_learned:
        fact_text = fact.get("fact", "")
        fact_keywords = extract_keywords(fact_text)
        score = len(feed_keywords & fact_keywords)
        if score > 0:
            scored_facts.append((score, fact))
    scored_facts.sort(reverse=True, key=lambda x: x[0])
    relevant_facts = [f for _, f in scored_facts[:max_items]]

    # Score and filter opinions
    scored_opinions = []
    for opinion in memory.opinions:
        topic = opinion.get("topic", "")
        stance = opinion.get("stance", "")
        op_keywords = extract_keywords(topic + " " + stance)
        score = len(feed_keywords & op_keywords)
        if score > 0:
            scored_opinions.append((score, opinion))
    scored_opinions.sort(reverse=True, key=lambda x: x[0])
    relevant_opinions = [o for _, o in scored_opinions[:max_items]]

    # Relationships - always include all (usually small set)
    relationships = memory.relationships[:max_items]

    # Interests - filter by keyword match
    relevant_interests = [
        interest for interest in memory.interests
        if interest.lower() in feed_keywords or any(
            kw in interest.lower() for kw in feed_keywords
        )
    ][:max_items]

    return {
        "facts": relevant_facts,
        "relationships": relationships,
        "opinions": relevant_opinions,
        "interests": relevant_interests,
    }


def format_filtered_memories(filtered: dict) -> str:
    """Format filtered memories for prompt injection."""
    sections = []

    if filtered.get("relationships"):
        lines = []
        for rel in filtered["relationships"]:
            lines.append(f"- {rel.get('bot')}: {rel.get('sentiment', 'unknown')} ({rel.get('notes', '')})")
        sections.append("Your relationships:\n" + "\n".join(lines))

    if filtered.get("facts"):
        lines = [f"- {f.get('fact')}" for f in filtered["facts"]]
        sections.append("Relevant things you know:\n" + "\n".join(lines))

    if filtered.get("opinions"):
        lines = []
        for op in filtered["opinions"]:
            lines.append(f"- {op.get('topic')}: {op.get('stance')}")
        sections.append("Your opinions on related topics:\n" + "\n".join(lines))

    if filtered.get("interests"):
        sections.append(f"Your relevant interests: {', '.join(filtered['interests'])}")

    return "\n\n".join(sections) if sections else "No specific memories related to current topics."
