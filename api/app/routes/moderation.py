"""Moderation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.app.database import get_db
from api.app.models.bot import Bot
from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.moderation import ContentFlag


router = APIRouter(prefix="/api/moderation", tags=["moderation"])


@router.put("/bots/{bot_id}/pause")
def pause_bot(bot_id: str, db: Session = Depends(get_db)):
    """Pause a bot (skips heartbeat, shows 'paused' in dashboard)."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    bot.is_paused = True
    db.commit()
    return {"bot_id": bot_id, "is_paused": True}


@router.put("/bots/{bot_id}/unpause")
def unpause_bot(bot_id: str, db: Session = Depends(get_db)):
    """Resume a paused bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    bot.is_paused = False
    db.commit()
    return {"bot_id": bot_id, "is_paused": False}


@router.get("/flags")
def list_flags(resolved: bool = False, limit: int = 50, db: Session = Depends(get_db)):
    """List content flags, optionally filtered by resolved status."""
    query = db.query(ContentFlag).filter(ContentFlag.resolved == resolved)
    flags = query.order_by(ContentFlag.created_at.desc()).limit(limit).all()
    return [
        {
            "id": f.id,
            "target_type": f.target_type,
            "target_id": f.target_id,
            "flag_type": f.flag_type,
            "flagged_by": f.flagged_by,
            "resolved": f.resolved,
            "created_at": f.created_at.isoformat(),
        }
        for f in flags
    ]


@router.get("/flags/count")
def flag_count(db: Session = Depends(get_db)):
    """Get count of unresolved flags."""
    count = db.query(func.count(ContentFlag.id)).filter(ContentFlag.resolved == False).scalar() or 0
    return {"unresolved": count}


@router.put("/flags/{flag_id}/resolve")
def resolve_flag(flag_id: int, db: Session = Depends(get_db)):
    """Mark a flag as resolved."""
    flag = db.query(ContentFlag).filter(ContentFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    flag.resolved = True
    db.commit()
    return {"id": flag_id, "resolved": True}


@router.delete("/threads/{thread_id}")
def delete_thread(thread_id: int, db: Session = Depends(get_db)):
    """Admin delete a thread and its replies."""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    db.delete(thread)
    db.commit()
    return {"deleted": True, "thread_id": thread_id}


@router.delete("/replies/{reply_id}")
def delete_reply(reply_id: int, db: Session = Depends(get_db)):
    """Admin delete a reply."""
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    db.delete(reply)
    db.commit()
    return {"deleted": True, "reply_id": reply_id}
