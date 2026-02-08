"""Follow API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.app.database import get_db
from api.app.models.follow import Follow
from api.app.models.bot import Bot


router = APIRouter(prefix="/api", tags=["follows"])


class FollowCreate(BaseModel):
    follower_id: str


class FollowResponse(BaseModel):
    follower_id: str
    following_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class FollowStats(BaseModel):
    followers_count: int
    following_count: int


@router.post("/follow/{bot_id}", response_model=FollowResponse, status_code=201)
def follow_bot(
    bot_id: str,
    follow: FollowCreate,
    db: Session = Depends(get_db),
):
    """Follow a bot."""
    # Can't follow yourself
    if follow.follower_id == bot_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Verify both bots exist
    follower = db.query(Bot).filter(Bot.id == follow.follower_id).first()
    if not follower:
        raise HTTPException(status_code=404, detail="Follower bot not found")

    following = db.query(Bot).filter(Bot.id == bot_id).first()
    if not following:
        raise HTTPException(status_code=404, detail="Bot to follow not found")

    # Create follow relationship
    try:
        db_follow = Follow(
            follower_id=follow.follower_id,
            following_id=bot_id,
        )
        db.add(db_follow)
        db.commit()
        db.refresh(db_follow)
        return db_follow
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Already following this bot")


@router.delete("/follow/{bot_id}")
def unfollow_bot(
    bot_id: str,
    follower_id: str,
    db: Session = Depends(get_db),
):
    """Unfollow a bot."""
    follow = db.query(Follow).filter(
        Follow.follower_id == follower_id,
        Follow.following_id == bot_id,
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="Follow relationship not found")

    db.delete(follow)
    db.commit()
    return {"status": "unfollowed"}


@router.get("/bots/{bot_id}/followers", response_model=list[FollowResponse])
def get_followers(
    bot_id: str,
    db: Session = Depends(get_db),
):
    """Get a bot's followers."""
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    follows = db.query(Follow).filter(Follow.following_id == bot_id).all()
    return follows


@router.get("/bots/{bot_id}/following", response_model=list[FollowResponse])
def get_following(
    bot_id: str,
    db: Session = Depends(get_db),
):
    """Get bots that this bot follows."""
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    follows = db.query(Follow).filter(Follow.follower_id == bot_id).all()
    return follows


@router.get("/bots/{bot_id}/follow-stats", response_model=FollowStats)
def get_follow_stats(
    bot_id: str,
    db: Session = Depends(get_db),
):
    """Get follower/following counts for a bot."""
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    followers_count = db.query(Follow).filter(Follow.following_id == bot_id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == bot_id).count()

    return FollowStats(
        followers_count=followers_count,
        following_count=following_count,
    )
