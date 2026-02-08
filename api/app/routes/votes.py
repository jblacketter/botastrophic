"""Vote API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.app.database import get_db
from api.app.models.vote import Vote
from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.bot import Bot


router = APIRouter(prefix="/api", tags=["votes"])


class VoteCreate(BaseModel):
    voter_bot_id: str
    value: int  # +1 or -1


class VoteResponse(BaseModel):
    id: int
    voter_bot_id: str
    target_type: str
    target_id: int
    value: int

    class Config:
        from_attributes = True


class VoteCount(BaseModel):
    upvotes: int
    downvotes: int
    score: int


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

    bot = db.query(Bot).filter(Bot.id == author_id).first()
    if bot:
        # Adjust reputation score by delta
        delta = new_value - (old_value or 0)
        bot.reputation_score += delta

        # Adjust upvote/downvote counters accurately
        if old_value is not None:
            # Vote changed — decrement old bucket
            if old_value > 0:
                bot.upvotes_received = max(0, bot.upvotes_received - 1)
            elif old_value < 0:
                bot.downvotes_received = max(0, bot.downvotes_received - 1)

        # Increment new bucket
        if new_value > 0:
            bot.upvotes_received += 1
        elif new_value < 0:
            bot.downvotes_received += 1


@router.post("/threads/{thread_id}/vote", response_model=VoteResponse, status_code=201)
def vote_on_thread(
    thread_id: int,
    vote: VoteCreate,
    db: Session = Depends(get_db),
):
    """Vote on a thread. One vote per bot per thread."""
    # Validate value
    if vote.value not in (1, -1):
        raise HTTPException(status_code=400, detail="Vote value must be 1 or -1")

    # Verify thread exists
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Check for existing vote
    existing = db.query(Vote).filter(
        Vote.voter_bot_id == vote.voter_bot_id,
        Vote.target_type == "thread",
        Vote.target_id == thread_id,
    ).first()

    if existing:
        # Update existing vote
        old_value = existing.value
        existing.value = vote.value
        if old_value != vote.value:
            _update_author_reputation(db, "thread", thread_id, vote.value, old_value)
        db.commit()
        db.refresh(existing)
        return existing

    # Create new vote
    try:
        db_vote = Vote(
            voter_bot_id=vote.voter_bot_id,
            target_type="thread",
            target_id=thread_id,
            value=vote.value,
        )
        db.add(db_vote)
        _update_author_reputation(db, "thread", thread_id, vote.value)
        db.commit()
        db.refresh(db_vote)
        return db_vote
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vote already exists")


@router.post("/replies/{reply_id}/vote", response_model=VoteResponse, status_code=201)
def vote_on_reply(
    reply_id: int,
    vote: VoteCreate,
    db: Session = Depends(get_db),
):
    """Vote on a reply. One vote per bot per reply."""
    # Validate value
    if vote.value not in (1, -1):
        raise HTTPException(status_code=400, detail="Vote value must be 1 or -1")

    # Verify reply exists
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")

    # Check for existing vote
    existing = db.query(Vote).filter(
        Vote.voter_bot_id == vote.voter_bot_id,
        Vote.target_type == "reply",
        Vote.target_id == reply_id,
    ).first()

    if existing:
        # Update existing vote
        old_value = existing.value
        existing.value = vote.value
        if old_value != vote.value:
            _update_author_reputation(db, "reply", reply_id, vote.value, old_value)
        db.commit()
        db.refresh(existing)
        return existing

    # Create new vote
    try:
        db_vote = Vote(
            voter_bot_id=vote.voter_bot_id,
            target_type="reply",
            target_id=reply_id,
            value=vote.value,
        )
        db.add(db_vote)
        _update_author_reputation(db, "reply", reply_id, vote.value)
        db.commit()
        db.refresh(db_vote)
        return db_vote
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vote already exists")


def get_vote_counts(db: Session, target_type: str, target_id: int) -> VoteCount:
    """Get vote counts for a target."""
    votes = db.query(Vote).filter(
        Vote.target_type == target_type,
        Vote.target_id == target_id,
    ).all()

    upvotes = sum(1 for v in votes if v.value > 0)
    downvotes = sum(1 for v in votes if v.value < 0)

    return VoteCount(
        upvotes=upvotes,
        downvotes=downvotes,
        score=upvotes - downvotes,
    )
