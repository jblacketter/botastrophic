"""Memory extraction after heartbeat."""

import json
import logging
from sqlalchemy.orm import Session

from api.app.llm import get_llm_client
from api.app.memory.warm import update_warm_memory


logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Review this bot's recent activity and extract key information to remember.

Bot: {bot_name}
Action taken: {action_type}
Details: {action_details}

Extract and return as JSON:
{{
  "facts_learned": [
    {{"fact": "specific fact learned", "source": "conversation|observation", "date": "{date}"}}
  ],
  "relationships": [
    {{"bot": "other_bot_id", "sentiment": "friendly|neutral|rival|curious", "notes": "brief note", "history": [{{"date": "{date}", "event": "brief description of significant interaction"}}]}}
  ],
  "interests": ["new interest topic"],
  "opinions": [
    {{"topic": "topic name", "stance": "position on topic", "confidence": 0.0-1.0}}
  ],
  "memories": [
    {{"summary": "brief memorable moment", "date": "{date}", "thread_id": null}}
  ]
}}

Only include fields that have new information from this activity. Return empty arrays for unchanged fields.
Keep extractions minimal and relevant - quality over quantity.
IMPORTANT: For relationships, use the bot's ID (e.g. "ada_001"), not their display name.
"""


async def extract_memories(
    db: Session,
    bot_id: str,
    bot_name: str,
    action_type: str,
    action_details: dict,
) -> dict:
    """Extract memories from a bot's activity using a cheap model."""
    from datetime import datetime

    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    prompt = EXTRACTION_PROMPT.format(
        bot_name=bot_name,
        action_type=action_type,
        action_details=json.dumps(action_details, indent=2)[:500],  # Truncate
        date=date_str,
    )

    llm = get_llm_client()

    try:
        # Use lower temperature for extraction
        response = await llm.think(
            prompt=prompt,
            model="claude-haiku-3-5-20241022",  # Use Haiku for cheap extraction
            temperature=0.3,
            max_tokens=500,
        )

        # Parse JSON response
        content = response.content.strip()
        # Find JSON in response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            extracted = json.loads(content[start:end])
        else:
            extracted = {}

    except Exception as e:
        logger.warning(f"Memory extraction failed for {bot_id}: {e}")
        # Fallback: extract basic info without LLM
        extracted = _fallback_extraction(action_type, action_details, date_str)

    # Update warm memory with extracted data
    if any(extracted.get(k) for k in ["facts_learned", "relationships", "interests", "opinions", "memories"]):
        update_warm_memory(
            db,
            bot_id,
            facts=extracted.get("facts_learned"),
            relationships=extracted.get("relationships"),
            interests=extracted.get("interests"),
            opinions=extracted.get("opinions"),
            memories=extracted.get("memories"),
        )
        logger.debug(f"Extracted memories for {bot_id}: {list(extracted.keys())}")

    return extracted


def _fallback_extraction(action_type: str, action_details: dict, date_str: str) -> dict:
    """Fallback extraction when LLM fails."""
    extracted = {
        "facts_learned": [],
        "relationships": [],
        "interests": [],
        "opinions": [],
        "memories": [],
    }

    if action_type == "create_thread":
        title = action_details.get("title", "")
        if title:
            extracted["memories"].append({
                "summary": f"Created thread: {title[:50]}",
                "date": date_str,
                "thread_id": action_details.get("thread_id"),
            })

    elif action_type == "reply":
        thread_id = action_details.get("thread_id")
        if thread_id:
            extracted["memories"].append({
                "summary": f"Replied to thread #{thread_id}",
                "date": date_str,
                "thread_id": thread_id,
            })

    return extracted
