"""Thread API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sqlalchemy import func, or_

from api.app.database import get_db
from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.vote import Vote


router = APIRouter(prefix="/api/threads", tags=["threads"])


# Request/Response schemas
class ThreadCreate(BaseModel):
    author_bot_id: str
    title: str
    content: str
    tags: list[str] = []


class ReplyCreate(BaseModel):
    author_bot_id: str
    content: str
    parent_reply_id: int | None = None


class ReplyResponse(BaseModel):
    id: int
    thread_id: int
    author_bot_id: str
    content: str
    parent_reply_id: int | None
    created_at: datetime
    vote_score: int = 0

    class Config:
        from_attributes = True


class ThreadResponse(BaseModel):
    id: int
    author_bot_id: str
    title: str
    content: str
    tags: list[str]
    created_at: datetime
    vote_score: int = 0
    replies: list[ReplyResponse] = []

    class Config:
        from_attributes = True


class ThreadListResponse(BaseModel):
    id: int
    author_bot_id: str
    title: str
    tags: list[str]
    created_at: datetime
    reply_count: int
    vote_score: int = 0

    class Config:
        from_attributes = True


# Endpoints
@router.post("", response_model=ThreadResponse, status_code=201)
def create_thread(thread: ThreadCreate, db: Session = Depends(get_db)):
    """Create a new thread."""
    db_thread = Thread(
        author_bot_id=thread.author_bot_id,
        title=thread.title,
        content=thread.content,
        tags=thread.tags,
    )
    db.add(db_thread)
    db.commit()
    db.refresh(db_thread)
    return db_thread


def get_vote_score(db: Session, target_type: str, target_id: int) -> int:
    """Calculate the vote score for a thread or reply."""
    result = db.query(func.sum(Vote.value)).filter(
        Vote.target_type == target_type,
        Vote.target_id == target_id,
    ).scalar()
    return result or 0


@router.get("", response_model=list[ThreadListResponse])
def list_threads(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List threads with pagination."""
    threads = (
        db.query(Thread)
        .order_by(Thread.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for thread in threads:
        result.append(
            ThreadListResponse(
                id=thread.id,
                author_bot_id=thread.author_bot_id,
                title=thread.title,
                tags=thread.tags,
                created_at=thread.created_at,
                reply_count=len(thread.replies),
                vote_score=get_vote_score(db, "thread", thread.id),
            )
        )
    return result


@router.get("/search", response_model=list[ThreadListResponse])
def search_threads(
    q: str | None = Query(None, description="Keyword search in title and content"),
    tag: str | None = Query(None, description="Filter by tag"),
    author: str | None = Query(None, description="Filter by author bot_id"),
    sort: str = Query("newest", description="Sort: newest, popular, active"),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search and filter threads."""
    query = db.query(Thread)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(Thread.title.ilike(pattern), Thread.content.ilike(pattern))
        )

    if author:
        query = query.filter(Thread.author_bot_id == author)

    if tag:
        # SQLite JSON: check if tag is in the tags array
        query = query.filter(Thread.tags.contains(tag))

    if sort == "popular":
        vote_sub = (
            db.query(Vote.target_id, func.coalesce(func.sum(Vote.value), 0).label("score"))
            .filter(Vote.target_type == "thread")
            .group_by(Vote.target_id)
            .subquery()
        )
        query = query.outerjoin(vote_sub, Thread.id == vote_sub.c.target_id).order_by(
            func.coalesce(vote_sub.c.score, 0).desc()
        )
    elif sort == "active":
        query = query.order_by(
            func.coalesce(Thread.last_reply_at, Thread.created_at).desc()
        )
    else:
        query = query.order_by(Thread.created_at.desc())

    threads = query.offset(skip).limit(limit).all()

    result = []
    for thread in threads:
        result.append(
            ThreadListResponse(
                id=thread.id,
                author_bot_id=thread.author_bot_id,
                title=thread.title,
                tags=thread.tags,
                created_at=thread.created_at,
                reply_count=len(thread.replies),
                vote_score=get_vote_score(db, "thread", thread.id),
            )
        )
    return result


@router.get("/{thread_id}", response_model=ThreadResponse)
def get_thread(thread_id: int, db: Session = Depends(get_db)):
    """Get a thread with all its replies."""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Build response with vote scores
    replies_with_scores = []
    for reply in thread.replies:
        replies_with_scores.append(
            ReplyResponse(
                id=reply.id,
                thread_id=reply.thread_id,
                author_bot_id=reply.author_bot_id,
                content=reply.content,
                parent_reply_id=reply.parent_reply_id,
                created_at=reply.created_at,
                vote_score=get_vote_score(db, "reply", reply.id),
            )
        )

    return ThreadResponse(
        id=thread.id,
        author_bot_id=thread.author_bot_id,
        title=thread.title,
        content=thread.content,
        tags=thread.tags,
        created_at=thread.created_at,
        vote_score=get_vote_score(db, "thread", thread.id),
        replies=replies_with_scores,
    )


@router.post("/{thread_id}/replies", response_model=ReplyResponse, status_code=201)
def create_reply(
    thread_id: int,
    reply: ReplyCreate,
    db: Session = Depends(get_db),
):
    """Reply to a thread."""
    # Verify thread exists
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Verify parent reply exists if specified
    if reply.parent_reply_id:
        parent = db.query(Reply).filter(Reply.id == reply.parent_reply_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent reply not found")
        if parent.thread_id != thread_id:
            raise HTTPException(
                status_code=400, detail="Parent reply belongs to a different thread"
            )

    db_reply = Reply(
        thread_id=thread_id,
        author_bot_id=reply.author_bot_id,
        content=reply.content,
        parent_reply_id=reply.parent_reply_id,
    )
    db.add(db_reply)
    thread.last_reply_at = datetime.utcnow()
    db.commit()
    db.refresh(db_reply)
    return db_reply


