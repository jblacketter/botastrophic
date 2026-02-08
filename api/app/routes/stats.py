"""Usage statistics API endpoints."""

from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String

from api.app.database import get_db
from api.app.models.usage import TokenUsage
from api.app.models.bot import Bot
from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.vote import Vote
from api.app.models.activity_log import ActivityLog
from api.app.models.warm_memory import WarmMemory
from api.app.models.cold_memory import ColdMemory
from api.app.usage import DAILY_TOKEN_CAP, DAILY_COST_CAP_USD


router = APIRouter(prefix="/api/stats", tags=["stats"])


class BotUsageResponse(BaseModel):
    bot_id: str
    bot_name: str
    date: date
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    token_cap: int
    cost_cap_usd: float
    cap_exceeded: bool


class UsageSummaryResponse(BaseModel):
    period: str
    bots: list[BotUsageResponse]
    total_tokens: int
    total_cost_usd: float


@router.get("/usage", response_model=UsageSummaryResponse)
def get_usage(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
):
    """Get per-bot usage statistics."""
    today = date.today()

    if period == "daily":
        start_date = today
    elif period == "weekly":
        start_date = today - timedelta(days=7)
    else:  # monthly
        start_date = today - timedelta(days=30)

    # Get all bots for name lookup
    bots = {b.id: b.name for b in db.query(Bot).all()}

    # Aggregate usage per bot
    rows = (
        db.query(
            TokenUsage.bot_id,
            func.sum(TokenUsage.input_tokens).label("input_tokens"),
            func.sum(TokenUsage.output_tokens).label("output_tokens"),
            func.sum(TokenUsage.estimated_cost_usd).label("cost"),
        )
        .filter(TokenUsage.date >= start_date)
        .group_by(TokenUsage.bot_id)
        .all()
    )

    bot_usage = []
    total_tokens = 0
    total_cost = 0.0

    for row in rows:
        inp = row.input_tokens or 0
        out = row.output_tokens or 0
        total = inp + out
        cost = row.cost or 0.0
        total_tokens += total
        total_cost += cost

        # Use per-bot cap overrides if set, otherwise global defaults
        bot_obj = db.query(Bot).filter(Bot.id == row.bot_id).first()
        token_cap = DAILY_TOKEN_CAP
        cost_cap = DAILY_COST_CAP_USD
        if bot_obj:
            if bot_obj.daily_token_cap is not None:
                token_cap = bot_obj.daily_token_cap
            if bot_obj.daily_cost_cap_usd is not None:
                cost_cap = bot_obj.daily_cost_cap_usd

        bot_usage.append(BotUsageResponse(
            bot_id=row.bot_id,
            bot_name=bots.get(row.bot_id, row.bot_id),
            date=today,
            input_tokens=inp,
            output_tokens=out,
            total_tokens=total,
            estimated_cost_usd=round(cost, 4),
            token_cap=token_cap,
            cost_cap_usd=cost_cap,
            cap_exceeded=total >= token_cap or cost >= cost_cap,
        ))

    return UsageSummaryResponse(
        period=period,
        bots=bot_usage,
        total_tokens=total_tokens,
        total_cost_usd=round(total_cost, 4),
    )


# --- Memory endpoints ---

@router.get("/bots/{bot_id}/memory/warm")
def get_warm_memory(
    bot_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return warm memory for a bot (facts, relationships, opinions, interests)."""
    memory = db.query(WarmMemory).filter(WarmMemory.bot_id == bot_id).first()
    if not memory:
        return {
            "bot_id": bot_id,
            "facts_learned": [],
            "relationships": [],
            "interests": [],
            "opinions": [],
            "memories": [],
        }
    return {
        "bot_id": bot_id,
        "facts_learned": memory.facts_learned[-limit:],
        "relationships": memory.relationships[-limit:],
        "interests": memory.interests[:limit],
        "opinions": memory.opinions[-limit:],
        "memories": memory.memories[-limit:],
    }


@router.get("/bots/{bot_id}/memory/cold")
def get_cold_memories(
    bot_id: str,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return cold memory summaries for a bot, paginated."""
    memories = (
        db.query(ColdMemory)
        .filter(ColdMemory.bot_id == bot_id)
        .order_by(ColdMemory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "period_start": str(m.period_start),
            "period_end": str(m.period_end),
            "summary": m.summary,
            "facts_compressed": m.facts_compressed,
            "memories_compressed": m.memories_compressed,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in memories
    ]


@router.get("/reputation")
def get_reputation(db: Session = Depends(get_db)):
    """Return current reputation scores for all bots."""
    bots = db.query(Bot).all()
    return [
        {
            "bot_id": b.id,
            "bot_name": b.name,
            "reputation_score": b.reputation_score,
            "upvotes_received": b.upvotes_received,
            "downvotes_received": b.downvotes_received,
        }
        for b in bots
    ]


@router.get("/reputation-history")
def get_reputation_history(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Return reputation scores over time, derived from activity log snapshots.

    Each heartbeat logs the bot's reputation_score in activity details.
    This endpoint returns one data point per bot per day (latest score that day).
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    bot_names = {b.id: b.name for b in db.query(Bot).all()}

    # Get activity logs that have reputation_score in details
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.created_at >= cutoff)
        .order_by(ActivityLog.created_at.asc())
        .all()
    )

    # Group by bot_id and date, keeping last score per day
    # Structure: {bot_id: {date_str: reputation_score}}
    daily_scores: dict[str, dict[str, int]] = {}
    for log in logs:
        if not log.details or "reputation_score" not in log.details:
            continue
        bot_id = log.bot_id
        day_str = log.created_at.strftime("%Y-%m-%d")
        if bot_id not in daily_scores:
            daily_scores[bot_id] = {}
        daily_scores[bot_id][day_str] = log.details["reputation_score"]

    # Build response: list of {bot_id, bot_name, series: [{date, score}]}
    result = []
    for bot_id, scores_by_day in daily_scores.items():
        series = [
            {"date": d, "score": s}
            for d, s in sorted(scores_by_day.items())
        ]
        result.append({
            "bot_id": bot_id,
            "bot_name": bot_names.get(bot_id, bot_id),
            "series": series,
        })

    return result


@router.get("/analytics")
def get_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Return aggregate analytics for the given period."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    total_threads = db.query(func.count(Thread.id)).filter(Thread.created_at >= cutoff).scalar() or 0
    total_replies = db.query(func.count(Reply.id)).filter(Reply.created_at >= cutoff).scalar() or 0
    total_votes = db.query(func.count(Vote.id)).filter(Vote.created_at >= cutoff).scalar() or 0

    # Posts per day
    logs = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.created_at >= cutoff,
            ActivityLog.action_type.in_(["create_thread", "reply"]),
        )
        .all()
    )
    daily: dict[str, dict[str, int]] = {}
    for log in logs:
        day_str = log.created_at.strftime("%Y-%m-%d")
        if day_str not in daily:
            daily[day_str] = {"threads": 0, "replies": 0}
        if log.action_type == "create_thread":
            daily[day_str]["threads"] += 1
        else:
            daily[day_str]["replies"] += 1
    posts_per_day = [{"date": d, **v} for d, v in sorted(daily.items())]

    # Most active bot
    active_bot = (
        db.query(ActivityLog.bot_id, func.count(ActivityLog.id).label("cnt"))
        .filter(
            ActivityLog.created_at >= cutoff,
            ActivityLog.action_type.in_(["create_thread", "reply"]),
        )
        .group_by(ActivityLog.bot_id)
        .order_by(func.count(ActivityLog.id).desc())
        .first()
    )
    most_active = active_bot.bot_id if active_bot else None

    # Engagement by bot
    bot_names = {b.id: b.name for b in db.query(Bot).all()}
    engagement_rows = (
        db.query(
            ActivityLog.bot_id,
            ActivityLog.action_type,
            func.count(ActivityLog.id).label("cnt"),
        )
        .filter(
            ActivityLog.created_at >= cutoff,
            ActivityLog.action_type.in_(["create_thread", "reply", "vote"]),
        )
        .group_by(ActivityLog.bot_id, ActivityLog.action_type)
        .all()
    )
    engagement: dict[str, dict[str, int]] = {}
    for row in engagement_rows:
        if row.bot_id not in engagement:
            engagement[row.bot_id] = {"threads": 0, "replies": 0, "votes": 0}
        key = {"create_thread": "threads", "reply": "replies", "vote": "votes"}.get(row.action_type, "")
        if key:
            engagement[row.bot_id][key] = row.cnt

    engagement_by_bot = [
        {"bot_id": bid, "bot_name": bot_names.get(bid, bid), **counts}
        for bid, counts in engagement.items()
    ]

    # Average replies per thread
    avg_replies = round(total_replies / max(total_threads, 1), 1)

    return {
        "period_days": days,
        "total_threads": total_threads,
        "total_replies": total_replies,
        "total_votes": total_votes,
        "posts_per_day": posts_per_day,
        "most_active_bot": most_active,
        "avg_replies_per_thread": avg_replies,
        "engagement_by_bot": engagement_by_bot,
    }


@router.get("/relationship-graph")
def get_relationship_graph(db: Session = Depends(get_db)):
    """Return nodes (bots) and edges (relationships) for graph visualization."""
    from api.app.models.follow import Follow

    bots = db.query(Bot).all()
    nodes = [
        {
            "id": b.id,
            "name": b.name,
            "reputation": b.reputation_score,
            "post_count": (
                (db.query(func.count(Thread.id)).filter(Thread.author_bot_id == b.id).scalar() or 0)
                + (db.query(func.count(Reply.id)).filter(Reply.author_bot_id == b.id).scalar() or 0)
            ),
        }
        for b in bots
    ]

    # Compute edges from votes between bot pairs
    bot_ids = [b.id for b in bots]
    edges = []
    seen_pairs: set[tuple[str, str]] = set()

    for i, src_id in enumerate(bot_ids):
        for tgt_id in bot_ids[i + 1:]:
            # Interaction count: replies from src to tgt's threads and vice versa
            src_to_tgt_replies = (
                db.query(func.count(Reply.id))
                .join(Thread, Reply.thread_id == Thread.id)
                .filter(Reply.author_bot_id == src_id, Thread.author_bot_id == tgt_id)
                .scalar() or 0
            )
            tgt_to_src_replies = (
                db.query(func.count(Reply.id))
                .join(Thread, Reply.thread_id == Thread.id)
                .filter(Reply.author_bot_id == tgt_id, Thread.author_bot_id == src_id)
                .scalar() or 0
            )
            interaction_count = src_to_tgt_replies + tgt_to_src_replies

            # Sentiment from votes: src voting on tgt's content
            src_votes_on_tgt = _net_votes_between(db, src_id, tgt_id)
            tgt_votes_on_src = _net_votes_between(db, tgt_id, src_id)
            total_vote_count = abs(src_votes_on_tgt) + abs(tgt_votes_on_src)
            sentiment = 0.0
            if total_vote_count > 0:
                sentiment = round((src_votes_on_tgt + tgt_votes_on_src) / total_vote_count, 2)
                sentiment = max(-1.0, min(1.0, sentiment))

            # Follows
            follows_forward = db.query(Follow).filter(
                Follow.follower_id == src_id, Follow.following_id == tgt_id
            ).first() is not None
            follows_backward = db.query(Follow).filter(
                Follow.follower_id == tgt_id, Follow.following_id == src_id
            ).first() is not None

            if interaction_count > 0 or follows_forward or follows_backward:
                edges.append({
                    "source": src_id,
                    "target": tgt_id,
                    "interaction_count": interaction_count,
                    "sentiment": sentiment,
                    "follows": follows_forward or follows_backward,
                })

    return {"nodes": nodes, "edges": edges}


def _net_votes_between(db: Session, voter_id: str, author_id: str) -> int:
    """Net votes from voter on author's content (threads + replies)."""
    # Votes on author's threads
    thread_votes = (
        db.query(func.coalesce(func.sum(Vote.value), 0))
        .join(Thread, (Vote.target_type == "thread") & (Vote.target_id == Thread.id))
        .filter(Vote.voter_bot_id == voter_id, Thread.author_bot_id == author_id)
        .scalar() or 0
    )
    # Votes on author's replies
    reply_votes = (
        db.query(func.coalesce(func.sum(Vote.value), 0))
        .join(Reply, (Vote.target_type == "reply") & (Vote.target_id == Reply.id))
        .filter(Vote.voter_bot_id == voter_id, Reply.author_bot_id == author_id)
        .scalar() or 0
    )
    return thread_votes + reply_votes
