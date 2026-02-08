"""Parse bot action responses from LLM output."""

import json
import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class BotAction:
    """Parsed action from bot response."""
    action: Literal["create_thread", "reply", "vote", "web_search", "do_nothing"]
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    thread_id: int | None = None
    reply_id: int | None = None
    parent_reply_id: int | None = None
    query: str | None = None
    reason: str | None = None
    vote_value: int | None = None  # 1 for upvote, -1 for downvote


def parse_bot_action(response_text: str) -> BotAction:
    """Extract JSON action from bot response, handling preamble."""
    # Try direct parse first
    try:
        data = json.loads(response_text.strip())
        return _dict_to_action(data)
    except json.JSONDecodeError:
        pass

    # Extract from markdown code fences (```json ... ``` or ``` ... ```)
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if fence_match:
        try:
            data = json.loads(fence_match.group(1))
            return _dict_to_action(data)
        except json.JSONDecodeError:
            pass

    # Look for JSON block in response (bot may include thinking)
    json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return _dict_to_action(data)
        except json.JSONDecodeError:
            pass

    # Try to find a more complex JSON object with nested braces
    json_match = re.search(r'\{.*"action".*\}', response_text, re.DOTALL)
    if json_match:
        # Find balanced braces
        text = json_match.group()
        depth = 0
        start = 0
        for i, char in enumerate(text):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(text[start:i+1])
                        return _dict_to_action(data)
                    except json.JSONDecodeError:
                        continue

    # Fallback: do nothing
    return BotAction(
        action="do_nothing",
        reason="Failed to parse bot response"
    )


def _dict_to_action(data: dict) -> BotAction:
    """Convert parsed dict to BotAction."""
    action_type = data.get("action", "do_nothing")

    if action_type == "create_thread":
        return BotAction(
            action="create_thread",
            title=data.get("title", "Untitled"),
            content=data.get("content", ""),
            tags=data.get("tags", []),
        )
    elif action_type == "reply":
        return BotAction(
            action="reply",
            thread_id=data.get("thread_id"),
            parent_reply_id=data.get("parent_reply_id"),
            content=data.get("content", ""),
        )
    elif action_type == "vote":
        return BotAction(
            action="vote",
            thread_id=data.get("thread_id"),
            reply_id=data.get("reply_id"),
            vote_value=data.get("value", 1),
            reason=data.get("reason", ""),
        )
    elif action_type == "web_search":
        return BotAction(
            action="web_search",
            query=data.get("query", ""),
            reason=data.get("reason", ""),
        )
    else:  # do_nothing or unknown
        return BotAction(
            action="do_nothing",
            reason=data.get("reason", "No specific reason"),
        )
