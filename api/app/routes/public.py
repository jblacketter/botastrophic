"""Public read-only API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.app.database import get_db
from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.vote import Vote
from api.app.models.bot import Bot
from api.app.models.activity_log import ActivityLog


router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/threads")
def public_threads(
    skip: int = 0,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Public thread list."""
    threads = (
        db.query(Thread)
        .order_by(Thread.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    result = []
    for t in threads:
        vote_score = db.query(func.coalesce(func.sum(Vote.value), 0)).filter(
            Vote.target_type == "thread", Vote.target_id == t.id
        ).scalar() or 0
        result.append({
            "id": t.id,
            "author_bot_id": t.author_bot_id,
            "title": t.title,
            "tags": t.tags,
            "created_at": t.created_at.isoformat(),
            "reply_count": len(t.replies),
            "vote_score": vote_score,
        })
    return result


@router.get("/threads/{thread_id}")
def public_thread(thread_id: int, db: Session = Depends(get_db)):
    """Public thread detail with replies."""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    vote_score = db.query(func.coalesce(func.sum(Vote.value), 0)).filter(
        Vote.target_type == "thread", Vote.target_id == thread.id
    ).scalar() or 0

    replies = []
    for r in thread.replies:
        r_score = db.query(func.coalesce(func.sum(Vote.value), 0)).filter(
            Vote.target_type == "reply", Vote.target_id == r.id
        ).scalar() or 0
        replies.append({
            "id": r.id,
            "author_bot_id": r.author_bot_id,
            "content": r.content,
            "parent_reply_id": r.parent_reply_id,
            "created_at": r.created_at.isoformat(),
            "vote_score": r_score,
        })

    return {
        "id": thread.id,
        "author_bot_id": thread.author_bot_id,
        "title": thread.title,
        "content": thread.content,
        "tags": thread.tags,
        "created_at": thread.created_at.isoformat(),
        "vote_score": vote_score,
        "replies": replies,
    }


@router.get("/bots")
def public_bots(db: Session = Depends(get_db)):
    """Public bot list (name, personality summary, reputation - no config)."""
    bots = db.query(Bot).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "reputation_score": b.reputation_score,
            "traits": (b.personality_config or {}).get("personality", {}).get("traits", []),
        }
        for b in bots
    ]


@router.get("/activity")
def public_activity(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Public activity feed (no internal details)."""
    logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "bot_id": log.bot_id,
            "action_type": log.action_type,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
