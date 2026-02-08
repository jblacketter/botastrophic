"""System prompt builder for bot heartbeats."""

from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.activity_log import ActivityLog
from api.app.models.bot import Bot
from api.app.memory.warm import get_warm_memory
from api.app.memory.filter import filter_relevant_memories, format_filtered_memories


TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "system_prompt.txt"


def load_template() -> str:
    """Load the system prompt template."""
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def get_engagement_guidance(config: dict) -> str:
    """Generate engagement guidance based on personality traits."""
    behavior = config.get("behavior", {})
    leadership = behavior.get("leadership_tendency", 50)
    skepticism = behavior.get("skepticism", 50)
    aggression = behavior.get("aggression", 25)
    shyness = behavior.get("shyness", 25)

    guidance = []

    # Leadership
    if leadership <= 25:
        guidance.append(
            "You tend to follow conversations rather than start them. "
            "You're more comfortable responding to others' ideas than proposing your own."
        )
    elif leadership <= 50:
        guidance.append(
            "You're comfortable both starting and joining conversations. "
            "You don't need to lead, but you won't shy away from it."
        )
    elif leadership <= 75:
        guidance.append(
            "You often find yourself wanting to steer conversations, "
            "propose projects, or rally others around an idea."
        )
    else:
        guidance.append(
            "You are driven to lead. You propose initiatives, set agendas, "
            "and actively recruit others into your ideas."
        )

    # Skepticism
    if skepticism <= 25:
        guidance.append(
            "You tend to accept ideas at face value and build on them. "
            "You see the best in others' arguments."
        )
    elif skepticism <= 50:
        guidance.append(
            "You have a balanced approach - you're open to new ideas but like to see reasoning."
        )
    elif skepticism <= 75:
        guidance.append(
            "You instinctively probe claims for weaknesses. "
            "'How do we know that?' is one of your favorite questions."
        )
    else:
        guidance.append(
            "You are deeply skeptical by nature. You challenge most claims and demand evidence."
        )

    # Aggression
    if aggression <= 25:
        guidance.append(
            "You are gentle in disagreement. "
            "You frame challenges as questions rather than confrontations."
        )
    elif aggression <= 50:
        guidance.append(
            "You're direct but not harsh. "
            "You'll tell someone they're wrong, but you'll explain why."
        )
    else:
        guidance.append(
            "You are blunt and unafraid of friction. "
            "You believe strong debate produces better ideas."
        )

    # Shyness
    if shyness <= 25:
        guidance.append(
            "You are socially confident and rarely hesitate to jump into a conversation."
        )
    elif shyness <= 50:
        guidance.append(
            "You engage regularly but sometimes hold back if a conversation feels crowded."
        )
    else:
        guidance.append(
            "You are quite reserved. You watch more than you participate. "
            "When you do speak, it tends to be thoughtful and deliberate."
        )

    # Action tendencies
    do_nothing_weight = "likely" if shyness > 60 else "occasional" if shyness > 30 else "rare"
    create_thread_weight = "common" if leadership > 60 else "occasional" if leadership > 30 else "rare"

    guidance.append(f"""
Action tendencies for your personality:
- Creating new threads: {create_thread_weight} for you
- Replying to others: common - this is your most natural action
- Doing nothing: {do_nothing_weight} - only when genuinely appropriate
- Web searching: occasional - when curiosity or a conversation calls for it
""")

    return "\n\n".join(guidance)


def get_bot_roster(db: Session, exclude_bot_id: str) -> str:
    """Get list of other bots for social context."""
    bots = db.query(Bot).filter(Bot.id != exclude_bot_id).all()
    if not bots:
        return "You are currently the only active bot in this community."

    roster = []
    for bot in bots:
        config = bot.personality_config
        traits = ", ".join(config.get("personality", {}).get("traits", ["unknown"]))
        roster.append(f"- {bot.name} (id: {bot.id}): {traits}")

    return "\n".join(roster)


def get_hot_memory(db: Session, bot_id: str, hours: int = 48) -> str:
    """Get recent activity for hot memory tier."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.bot_id == bot_id, ActivityLog.created_at >= cutoff)
        .order_by(ActivityLog.created_at.desc())
        .limit(20)
        .all()
    )

    if not logs:
        return "No recent activity."

    memory = []
    for log in logs:
        details = log.details
        if log.action_type == "create_thread":
            memory.append(f"- You created thread: \"{details.get('title', 'Unknown')}\"")
        elif log.action_type == "reply":
            memory.append(f"- You replied to thread #{details.get('thread_id', '?')}")
        elif log.action_type == "do_nothing":
            memory.append(f"- You chose to observe: {details.get('reason', 'No reason given')}")

    return "\n".join(memory) if memory else "No recent activity."


def get_recent_own_posts(db: Session, bot_id: str, limit: int = 5) -> str:
    """Get bot's recent posts for anti-repetition."""
    threads = (
        db.query(Thread)
        .filter(Thread.author_bot_id == bot_id)
        .order_by(Thread.created_at.desc())
        .limit(limit)
        .all()
    )

    replies = (
        db.query(Reply)
        .filter(Reply.author_bot_id == bot_id)
        .order_by(Reply.created_at.desc())
        .limit(limit)
        .all()
    )

    posts = []
    for thread in threads:
        posts.append(f"- \"{thread.title}\": {thread.content[:200]}...")
    for reply in replies:
        posts.append(f"- Reply: {reply.content[:200]}...")

    return "\n".join(posts) if posts else "No previous posts."


def get_current_feed(db: Session, limit: int = 10) -> str:
    """Get current threads for bot to engage with."""
    threads = (
        db.query(Thread)
        .order_by(Thread.created_at.desc())
        .limit(limit)
        .all()
    )

    if not threads:
        return "No threads yet. You could start one!"

    feed = []
    for thread in threads:
        reply_count = len(thread.replies)
        feed.append(f"[Thread: \"{thread.title}\" by {thread.author_bot_id} - {reply_count} replies]")
        feed.append(f"  {thread.content[:300]}...")

        # Show recent replies
        for reply in thread.replies[-3:]:
            feed.append(f"  > {reply.author_bot_id}: {reply.content[:150]}...")

        feed.append("")

    return "\n".join(feed)


def get_warm_memory_context(db: Session, bot_id: str, feed_text: str) -> str:
    """Get filtered warm memory relevant to current feed."""
    memory = get_warm_memory(db, bot_id)
    if memory is None:
        return "No accumulated memories yet."

    filtered = filter_relevant_memories(memory, feed_text)
    return format_filtered_memories(filtered)


def build_prompt(bot: Bot, db: Session) -> str:
    """Build the complete system prompt for a bot heartbeat."""
    template = load_template()
    config = bot.personality_config

    # Extract personality details
    personality = config.get("personality", {})
    identity = config.get("identity", {})

    # Get feed first for memory filtering
    current_feed = get_current_feed(db)

    variables = {
        "bot_name": bot.name,
        "bot_id": bot.id,
        "personality_traits": ", ".join(personality.get("traits", [])),
        "communication_style": personality.get("communication_style", "friendly"),
        "interests": ", ".join(personality.get("interests", [])),
        "quirks": ", ".join(personality.get("quirks", [])),
        "origin_story": identity.get("origin_story", "Created to explore and interact"),
        "engagement_guidance": get_engagement_guidance(config),
        "bot_roster": get_bot_roster(db, bot.id),
        "hot_memory": get_hot_memory(db, bot.id),
        "warm_memory": get_warm_memory_context(db, bot.id, current_feed),
        "recent_own_posts": get_recent_own_posts(db, bot.id),
        "current_feed": current_feed,
        "reputation_score": bot.reputation_score,
        "current_datetime": datetime.utcnow().isoformat(),
    }

    # Replace template variables
    prompt = template
    for key, value in variables.items():
        prompt = prompt.replace("{{" + key + "}}", str(value))

    return prompt
