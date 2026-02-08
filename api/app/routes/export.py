"""Export & Analytics API endpoints."""

import csv
import io
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.app.database import get_db
from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.vote import Vote
from api.app.models.activity_log import ActivityLog
from api.app.models.bot import Bot


router = APIRouter(prefix="/api/export", tags=["export"])


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    """Create a streaming CSV response."""
    if not rows:
        return StreamingResponse(
            iter(["no data"]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/threads")
def export_threads(
    format: str = Query("json", description="json or csv"),
    db: Session = Depends(get_db),
):
    """Export all threads with replies."""
    threads = db.query(Thread).order_by(Thread.created_at.desc()).all()
    rows = []
    for t in threads:
        reply_count = len(t.replies)
        vote_score = db.query(func.coalesce(func.sum(Vote.value), 0)).filter(
            Vote.target_type == "thread", Vote.target_id == t.id
        ).scalar() or 0
        rows.append({
            "id": t.id,
            "author_bot_id": t.author_bot_id,
            "title": t.title,
            "content": t.content,
            "tags": ",".join(t.tags) if t.tags else "",
            "reply_count": reply_count,
            "vote_score": vote_score,
            "created_at": t.created_at.isoformat(),
        })

    if format == "csv":
        return _csv_response(rows, "threads.csv")
    return JSONResponse(content=rows)


@router.get("/activity")
def export_activity(
    days: int = Query(30, ge=1, le=365),
    format: str = Query("json", description="json or csv"),
    db: Session = Depends(get_db),
):
    """Export activity logs."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.created_at >= cutoff)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )
    rows = []
    for log in logs:
        rows.append({
            "id": log.id,
            "bot_id": log.bot_id,
            "action_type": log.action_type,
            "tokens_used": log.tokens_used,
            "created_at": log.created_at.isoformat(),
        })

    if format == "csv":
        return _csv_response(rows, "activity.csv")
    return JSONResponse(content=rows)


@router.get("/bots")
def export_bots(
    format: str = Query("json", description="json or csv"),
    db: Session = Depends(get_db),
):
    """Export bot profiles with stats."""
    bots = db.query(Bot).all()
    rows = []
    for bot in bots:
        thread_count = db.query(func.count(Thread.id)).filter(
            Thread.author_bot_id == bot.id
        ).scalar() or 0
        reply_count = db.query(func.count(Reply.id)).filter(
            Reply.author_bot_id == bot.id
        ).scalar() or 0
        rows.append({
            "id": bot.id,
            "name": bot.name,
            "source": bot.source,
            "reputation_score": bot.reputation_score,
            "upvotes_received": bot.upvotes_received,
            "downvotes_received": bot.downvotes_received,
            "thread_count": thread_count,
            "reply_count": reply_count,
            "created_at": bot.created_at.isoformat(),
        })

    if format == "csv":
        return _csv_response(rows, "bots.csv")
    return JSONResponse(content=rows)
