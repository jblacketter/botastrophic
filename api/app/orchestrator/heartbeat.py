"""Heartbeat logic for bot actions."""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.app.models.bot import Bot
from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.activity_log import ActivityLog
from api.app.models.vote import Vote
from api.app.models.moderation import ContentFlag
from api.app.llm import get_llm_client
from api.app.orchestrator.prompt_builder import build_prompt
from api.app.orchestrator.action_parser import parse_bot_action, BotAction
from api.app.memory.extractor import extract_memories
from api.app.memory.cold import maybe_compress_to_cold
from api.app.memory.warm import record_interaction
from api.app.tools.web_search import WikipediaSearchTool
from api.app.usage import check_usage_cap, record_usage
from api.app.routes.ws import manager as ws_manager


logger = logging.getLogger(__name__)

_wiki_search = WikipediaSearchTool()

# Stopwords for Jaccard overlap
_STOPWORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from and or but "
    "not no nor so yet both either neither each every all any few more most other "
    "some such that this these those i me my we us our you your he him his she her "
    "it its they them their what which who whom how when where why am if then than".split()
)


def _jaccard_overlap(text_a: str, text_b: str) -> float:
    """Compute Jaccard word overlap between two texts."""
    words_a = set(text_a.lower().split()) - _STOPWORDS
    words_b = set(text_b.lower().split()) - _STOPWORDS
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _run_auto_moderation(db: Session, bot_id: str, action: BotAction, result: dict):
    """Run auto-moderation checks after a bot action. Creates ContentFlag if issues found."""
    if action.action not in ("create_thread", "reply"):
        return

    content = action.content or ""

    # Low quality: under 20 characters
    if len(content.strip()) < 20:
        target_type = "thread" if action.action == "create_thread" else "reply"
        target_id = result.get("thread_id") if action.action == "create_thread" else result.get("reply_id")
        if target_id:
            flag = ContentFlag(
                target_type=target_type,
                target_id=target_id,
                flag_type="low_quality",
                flagged_by="auto",
            )
            db.add(flag)
            logger.info(f"Auto-flag: low quality content from {bot_id}")

    # Repetition: Jaccard overlap > 0.6 with last 3 posts
    recent_logs = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.bot_id == bot_id,
            ActivityLog.action_type.in_(["create_thread", "reply"]),
        )
        .order_by(ActivityLog.created_at.desc())
        .limit(3)
        .all()
    )
    for log_entry in recent_logs:
        prev_content = (log_entry.details or {}).get("raw_response", "")
        if prev_content and _jaccard_overlap(content, prev_content) > 0.6:
            target_type = "thread" if action.action == "create_thread" else "reply"
            target_id = result.get("thread_id") if action.action == "create_thread" else result.get("reply_id")
            if target_id:
                flag = ContentFlag(
                    target_type=target_type,
                    target_id=target_id,
                    flag_type="repetitive",
                    flagged_by="auto",
                )
                db.add(flag)
                logger.info(f"Auto-flag: repetitive content from {bot_id}")
            break  # One flag per action is enough

    # Frequency cap: 5+ posts in the last hour
    one_hour_ago = datetime.utcnow().replace(microsecond=0)
    from datetime import timedelta
    one_hour_ago = one_hour_ago - timedelta(hours=1)
    recent_count = (
        db.query(func.count(ActivityLog.id))
        .filter(
            ActivityLog.bot_id == bot_id,
            ActivityLog.action_type.in_(["create_thread", "reply"]),
            ActivityLog.created_at >= one_hour_ago,
        )
        .scalar() or 0
    )
    if recent_count >= 5:
        target_type = "thread" if action.action == "create_thread" else "reply"
        target_id = result.get("thread_id") if action.action == "create_thread" else result.get("reply_id")
        if target_id:
            flag = ContentFlag(
                target_type=target_type,
                target_id=target_id,
                flag_type="frequency",
                flagged_by="auto",
            )
            db.add(flag)
            logger.info(f"Auto-flag: frequency cap for {bot_id}")

    db.commit()


def _update_author_reputation(
    db: Session, target_type: str, target_id: int, new_value: int, old_value: int | None = None,
):
    """Update cached reputation on the content author's Bot record.

    Args:
        old_value: Previous vote value (None for new votes).
        new_value: New vote value (+1 or -1).
    """
    if target_type == "thread":
        author_id = db.query(Thread.author_bot_id).filter(Thread.id == target_id).scalar()
    else:
        author_id = db.query(Reply.author_bot_id).filter(Reply.id == target_id).scalar()

    if not author_id:
        return

    author = db.query(Bot).filter(Bot.id == author_id).first()
    if author:
        delta = new_value - (old_value or 0)
        author.reputation_score += delta

        if old_value is not None:
            if old_value > 0:
                author.upvotes_received = max(0, author.upvotes_received - 1)
            elif old_value < 0:
                author.downvotes_received = max(0, author.downvotes_received - 1)

        if new_value > 0:
            author.upvotes_received += 1
        elif new_value < 0:
            author.downvotes_received += 1


async def execute_action(bot: Bot, action: BotAction, db: Session) -> dict:
    """Execute the bot's chosen action."""
    result = {"success": False, "action": action.action}

    if action.action == "create_thread":
        thread = Thread(
            author_bot_id=bot.id,
            title=action.title or "Untitled",
            content=action.content or "",
            tags=action.tags or [],
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
        result = {
            "success": True,
            "action": "create_thread",
            "thread_id": thread.id,
            "title": thread.title,
        }
        logger.info(f"Bot {bot.id} created thread: {thread.title}")

    elif action.action == "reply":
        if action.thread_id:
            reply = Reply(
                thread_id=action.thread_id,
                author_bot_id=bot.id,
                content=action.content or "",
                parent_reply_id=action.parent_reply_id,
            )
            db.add(reply)
            db.commit()
            db.refresh(reply)
            # Update last_reply_at on the parent thread
            parent_thread = db.query(Thread).filter(Thread.id == action.thread_id).first()
            if parent_thread:
                parent_thread.last_reply_at = datetime.utcnow()
                db.commit()
            result = {
                "success": True,
                "action": "reply",
                "reply_id": reply.id,
                "thread_id": action.thread_id,
                "content": (action.content or "")[:200],
            }
            # Record interaction with thread author
            thread_obj = db.query(Thread).filter(Thread.id == action.thread_id).first()
            if thread_obj and thread_obj.author_bot_id != bot.id:
                event = f"Replied to thread \"{thread_obj.title[:50]}\""
                record_interaction(db, bot.id, thread_obj.author_bot_id, event=event)
                result["other_bot_id"] = thread_obj.author_bot_id
            # Record interaction with parent reply author if replying to a specific reply
            if action.parent_reply_id:
                parent = db.query(Reply).filter(Reply.id == action.parent_reply_id).first()
                if parent and parent.author_bot_id != bot.id:
                    event = f"Replied to their comment in thread #{action.thread_id}"
                    record_interaction(db, bot.id, parent.author_bot_id, event=event)
                    result["other_bot_id"] = parent.author_bot_id
            logger.info(f"Bot {bot.id} replied to thread {action.thread_id}")
        else:
            result = {"success": False, "action": "reply", "error": "No thread_id provided"}

    elif action.action == "web_search":
        query = action.query or ""
        if query:
            try:
                search_results = await _wiki_search.search(query, max_results=3)
                result = {
                    "success": True,
                    "action": "web_search",
                    "query": query,
                    "results": search_results,
                    "result_count": len(search_results),
                }
                logger.info(f"Bot {bot.id} searched Wikipedia for: {query} ({len(search_results)} results)")
            except Exception as e:
                logger.warning(f"Wikipedia search failed for bot {bot.id}: {e}")
                result = {
                    "success": False,
                    "action": "web_search",
                    "query": query,
                    "error": str(e),
                }
        else:
            result = {"success": False, "action": "web_search", "error": "No query provided"}

    elif action.action == "vote":
        # Determine target type and id
        if action.thread_id:
            target_type = "thread"
            target_id = action.thread_id
        elif action.reply_id:
            target_type = "reply"
            target_id = action.reply_id
        else:
            return {"success": False, "action": "vote", "error": "No target specified"}

        # Clamp vote value to -1 or 1 to prevent LLM drift
        raw_vote = action.vote_value or 1
        vote_value = 1 if raw_vote > 0 else -1

        # Check for existing vote
        existing = db.query(Vote).filter(
            Vote.voter_bot_id == bot.id,
            Vote.target_type == target_type,
            Vote.target_id == target_id,
        ).first()

        if existing:
            # Update existing vote
            old_value = existing.value
            existing.value = vote_value
            if old_value != vote_value:
                _update_author_reputation(db, target_type, target_id, vote_value, old_value)
            db.commit()
            result = {
                "success": True,
                "action": "vote",
                "target_type": target_type,
                "target_id": target_id,
                "value": existing.value,
                "updated": True,
            }
        else:
            # Create new vote
            vote = Vote(
                voter_bot_id=bot.id,
                target_type=target_type,
                target_id=target_id,
                value=vote_value,
            )
            db.add(vote)
            _update_author_reputation(db, target_type, target_id, vote_value)
            db.commit()
            result = {
                "success": True,
                "action": "vote",
                "target_type": target_type,
                "target_id": target_id,
                "value": vote.value,
            }
        # Record interaction with the content author
        vote_label = "upvoted" if vote_value > 0 else "downvoted"
        if target_type == "thread":
            vote_target = db.query(Thread).filter(Thread.id == target_id).first()
            if vote_target and vote_target.author_bot_id != bot.id:
                event = f"{vote_label.capitalize()} their thread \"{vote_target.title[:50]}\""
                record_interaction(db, bot.id, vote_target.author_bot_id, event=event)
                result["other_bot_id"] = vote_target.author_bot_id
        elif target_type == "reply":
            vote_target = db.query(Reply).filter(Reply.id == target_id).first()
            if vote_target and vote_target.author_bot_id != bot.id:
                event = f"{vote_label.capitalize()} their reply in thread #{vote_target.thread_id}"
                record_interaction(db, bot.id, vote_target.author_bot_id, event=event)
                result["other_bot_id"] = vote_target.author_bot_id
        logger.info(f"Bot {bot.id} voted on {target_type} {target_id}")

    elif action.action == "do_nothing":
        result = {
            "success": True,
            "action": "do_nothing",
            "reason": action.reason,
        }
        logger.info(f"Bot {bot.id} chose to do nothing: {action.reason}")

    return result


async def heartbeat(bot_id: str, db: Session) -> dict:
    """Execute a single heartbeat for a bot."""
    logger.info(f"Starting heartbeat for bot {bot_id}")

    # Get bot
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        logger.error(f"Bot {bot_id} not found")
        return {"success": False, "error": "Bot not found"}

    # Check if bot is paused
    if bot.is_paused:
        log = ActivityLog(
            bot_id=bot_id,
            action_type="do_nothing",
            details={"reason": "Bot is paused by admin", "paused": True},
            tokens_used=0,
        )
        db.add(log)
        db.commit()
        logger.info(f"Bot {bot_id} is paused, skipping heartbeat")
        return {"success": True, "action": "do_nothing", "reason": "Bot is paused by admin"}

    # Check daily usage cap before calling LLM
    allowed, cap_reason = check_usage_cap(db, bot_id)
    if not allowed:
        log = ActivityLog(
            bot_id=bot_id,
            action_type="do_nothing",
            details={"reason": cap_reason, "cap_exceeded": True},
            tokens_used=0,
        )
        db.add(log)
        db.commit()
        logger.info(f"Bot {bot_id} capped: {cap_reason}")
        return {"success": True, "action": "do_nothing", "reason": cap_reason}

    # Build prompt
    prompt = build_prompt(bot, db)

    # Get LLM config from bot
    model_config = bot.personality_config.get("model", {})
    model = model_config.get("model", "claude-sonnet-4-5-20250929")
    temperature = model_config.get("temperature", 0.8)
    max_tokens = model_config.get("max_tokens", 1000)

    # Call LLM
    llm = get_llm_client()
    try:
        response = await llm.think(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        logger.error(f"LLM call failed for bot {bot_id}: {e}")
        return {"success": False, "error": str(e)}

    # Record token usage
    from api.app.config import get_settings
    provider = get_settings().llm_provider
    record_usage(db, bot_id, response.input_tokens, response.output_tokens, provider)

    # Parse action
    action = parse_bot_action(response.content)

    # Execute action
    result = await execute_action(bot, action, db)

    # Run auto-moderation checks
    try:
        _run_auto_moderation(db, bot_id, action, result)
    except Exception as e:
        logger.warning(f"Auto-moderation failed for {bot_id}: {e}")

    # Log activity (include reputation_score for time-series tracking)
    db.refresh(bot)
    log = ActivityLog(
        bot_id=bot_id,
        action_type=action.action,
        details={
            **result,
            "raw_response": response.content[:500],  # Truncate for storage
            "reputation_score": bot.reputation_score,
        },
        tokens_used=response.input_tokens + response.output_tokens,
    )
    db.add(log)
    db.commit()

    # Store web search results as facts in warm memory
    if result.get("success") and action.action == "web_search":
        from api.app.memory.warm import update_warm_memory

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        search_facts = []
        for sr in result.get("results", []):
            extract = sr.get("extract", "")
            if extract:
                search_facts.append({
                    "fact": extract[:200],
                    "source": "wikipedia",
                    "date": date_str,
                })
        if search_facts:
            try:
                update_warm_memory(db, bot_id, facts=search_facts)
                logger.debug(f"Stored {len(search_facts)} Wikipedia facts for {bot_id}")
            except Exception as e:
                logger.warning(f"Failed to store search facts for {bot_id}: {e}")

    # Extract memories from this activity (async, non-blocking)
    if result.get("success") and action.action in ["create_thread", "reply", "vote"]:
        try:
            await extract_memories(
                db=db,
                bot_id=bot_id,
                bot_name=bot.name,
                action_type=action.action,
                action_details=result,
            )
        except Exception as e:
            logger.warning(f"Memory extraction failed for {bot_id}: {e}")

    # Check if warm memory needs compression to cold
    try:
        await maybe_compress_to_cold(db, bot_id)
    except Exception as e:
        logger.warning(f"Cold memory compression check failed for {bot_id}: {e}")

    # Broadcast to WebSocket clients
    try:
        await ws_manager.broadcast({
            "type": "heartbeat_complete",
            "bot_id": bot_id,
            "bot_name": bot.name,
            "action": action.action,
            "details": {k: v for k, v in result.items() if k != "raw_response"},
            "tokens_used": response.input_tokens + response.output_tokens,
            "timestamp": datetime.utcnow().isoformat(),
        })
    except Exception as e:
        logger.debug(f"WebSocket broadcast failed: {e}")

    logger.info(f"Heartbeat complete for bot {bot_id}: {action.action}")
    return result
