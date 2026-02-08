"""Cost tracking and daily usage caps."""

import logging
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.app.models.usage import TokenUsage
from api.app.models.bot import Bot

logger = logging.getLogger(__name__)

# Daily caps per bot
DAILY_TOKEN_CAP = 100_000
DAILY_COST_CAP_USD = 1.00

# Approximate pricing per 1M tokens (Anthropic Sonnet)
COST_PER_1M_INPUT = 3.00
COST_PER_1M_OUTPUT = 15.00


def estimate_cost(input_tokens: int, output_tokens: int, provider: str = "anthropic") -> float:
    """Estimate cost in USD for token usage."""
    if provider == "ollama":
        return 0.0  # Local models are free
    if provider == "mock":
        return 0.0
    # Anthropic pricing
    return (input_tokens * COST_PER_1M_INPUT + output_tokens * COST_PER_1M_OUTPUT) / 1_000_000


def record_usage(
    db: Session,
    bot_id: str,
    input_tokens: int,
    output_tokens: int,
    provider: str,
) -> TokenUsage:
    """Record token usage for a bot. Upserts into today's row."""
    today = date.today()

    existing = db.query(TokenUsage).filter(
        TokenUsage.bot_id == bot_id,
        TokenUsage.date == today,
        TokenUsage.provider == provider,
    ).first()

    cost = estimate_cost(input_tokens, output_tokens, provider)

    if existing:
        existing.input_tokens += input_tokens
        existing.output_tokens += output_tokens
        existing.estimated_cost_usd += cost
        db.commit()
        return existing

    usage = TokenUsage(
        bot_id=bot_id,
        date=today,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=cost,
        provider=provider,
    )
    db.add(usage)
    db.commit()
    return usage


def get_today_usage(db: Session, bot_id: str) -> dict:
    """Get aggregated usage for a bot today across all providers."""
    today = date.today()
    rows = db.query(TokenUsage).filter(
        TokenUsage.bot_id == bot_id,
        TokenUsage.date == today,
    ).all()

    total_input = sum(r.input_tokens for r in rows)
    total_output = sum(r.output_tokens for r in rows)
    total_cost = sum(r.estimated_cost_usd for r in rows)

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "estimated_cost_usd": total_cost,
    }


def check_usage_cap(db: Session, bot_id: str) -> tuple[bool, str | None]:
    """Check if bot is within daily limits. Returns (allowed, reason).

    Per-bot overrides (daily_token_cap, daily_cost_cap_usd on Bot model)
    take precedence over global defaults when set (non-NULL).
    """
    # Check per-bot overrides
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    token_cap = DAILY_TOKEN_CAP
    cost_cap = DAILY_COST_CAP_USD
    if bot:
        if bot.daily_token_cap is not None:
            token_cap = bot.daily_token_cap
        if bot.daily_cost_cap_usd is not None:
            cost_cap = bot.daily_cost_cap_usd

    usage = get_today_usage(db, bot_id)
    total_tokens = usage["total_tokens"]

    if total_tokens >= token_cap:
        return False, f"Daily token cap reached ({total_tokens}/{token_cap})"
    if usage["estimated_cost_usd"] >= cost_cap:
        return False, f"Daily cost cap reached (${usage['estimated_cost_usd']:.2f}/${cost_cap:.2f})"
    return True, None
