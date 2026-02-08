"""Bot API endpoints."""

import random
import re
import string
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from sqlalchemy import func

from api.app.config import get_settings
from api.app.database import get_db
from api.app.models.bot import Bot
from api.app.models.thread import Thread
from api.app.models.reply import Reply
from api.app.models.follow import Follow


router = APIRouter(prefix="/api/bots", tags=["bots"])


# Request/Response schemas
class BotCreate(BaseModel):
    id: str
    name: str
    personality_config: dict = {}


class PersonalityConfig(BaseModel):
    traits: list[str] = Field(min_length=1, max_length=10)
    communication_style: str = "friendly and direct"
    engagement_style: str = "active"
    interests: list[str] = Field(default_factory=list)
    quirks: list[str] = Field(default_factory=list)
    creativity_level: int = Field(default=50, ge=0, le=100)
    leadership_tendency: int = Field(default=50, ge=0, le=100)
    skepticism: int = Field(default=50, ge=0, le=100)
    aggression: int = Field(default=20, ge=0, le=100)
    shyness: int = Field(default=30, ge=0, le=100)


class ModelConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = Field(default=0.8, ge=0, le=2)
    max_tokens: int = Field(default=1000, ge=100, le=4096)


class CustomBotCreate(BaseModel):
    name: str = Field(min_length=3, max_length=30)
    personality: PersonalityConfig
    model: ModelConfig | None = None


class BotResponse(BaseModel):
    id: str
    name: str
    personality_config: dict
    reputation_score: int = 0
    upvotes_received: int = 0
    downvotes_received: int = 0
    source: str = "yaml"
    is_paused: bool = False
    created_at: datetime
    follower_count: int = 0
    following_count: int = 0

    class Config:
        from_attributes = True


class BotPostResponse(BaseModel):
    type: str  # "thread" or "reply"
    id: int
    content: str
    created_at: datetime


# Endpoints
@router.post("", response_model=BotResponse, status_code=201)
def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    """Create a new bot (typically done at startup from config)."""
    existing = db.query(Bot).filter(Bot.id == bot.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Bot already exists")

    db_bot = Bot(
        id=bot.id,
        name=bot.name,
        personality_config=bot.personality_config,
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot


def get_follower_counts(db: Session, bot_id: str) -> tuple[int, int]:
    """Get follower and following counts for a bot."""
    followers = db.query(func.count(Follow.id)).filter(
        Follow.following_id == bot_id
    ).scalar() or 0
    following = db.query(func.count(Follow.id)).filter(
        Follow.follower_id == bot_id
    ).scalar() or 0
    return followers, following


@router.get("", response_model=list[BotResponse])
def list_bots(db: Session = Depends(get_db)):
    """List all bots."""
    bots = db.query(Bot).all()
    result = []
    for bot in bots:
        followers, following = get_follower_counts(db, bot.id)
        result.append(
            BotResponse(
                id=bot.id,
                name=bot.name,
                personality_config=bot.personality_config,
                reputation_score=bot.reputation_score,
                upvotes_received=bot.upvotes_received,
                downvotes_received=bot.downvotes_received,
                source=bot.source,
                is_paused=bot.is_paused,
                created_at=bot.created_at,
                follower_count=followers,
                following_count=following,
            )
        )
    return result


@router.get("/{bot_id}", response_model=BotResponse)
def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Get a bot by ID."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    followers, following = get_follower_counts(db, bot_id)
    return BotResponse(
        id=bot.id,
        name=bot.name,
        personality_config=bot.personality_config,
        reputation_score=bot.reputation_score,
        upvotes_received=bot.upvotes_received,
        downvotes_received=bot.downvotes_received,
        source=bot.source,
        is_paused=bot.is_paused,
        created_at=bot.created_at,
        follower_count=followers,
        following_count=following,
    )


@router.get("/{bot_id}/posts", response_model=list[BotPostResponse])
def get_bot_posts(
    bot_id: str,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """Get a bot's recent posts (threads and replies) for anti-repetition context."""
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Get recent threads
    threads = (
        db.query(Thread)
        .filter(Thread.author_bot_id == bot_id)
        .order_by(Thread.created_at.desc())
        .limit(limit)
        .all()
    )

    # Get recent replies
    replies = (
        db.query(Reply)
        .filter(Reply.author_bot_id == bot_id)
        .order_by(Reply.created_at.desc())
        .limit(limit)
        .all()
    )

    # Combine and sort by created_at
    posts = []
    for thread in threads:
        posts.append(
            BotPostResponse(
                type="thread",
                id=thread.id,
                content=f"{thread.title}: {thread.content}",
                created_at=thread.created_at,
            )
        )
    for reply in replies:
        posts.append(
            BotPostResponse(
                type="reply",
                id=reply.id,
                content=reply.content,
                created_at=reply.created_at,
            )
        )

    # Sort by date and limit
    posts.sort(key=lambda x: x.created_at, reverse=True)
    return posts[:limit]


def _generate_bot_id(name: str) -> str:
    """Generate a bot ID from name: lowercase + random suffix."""
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=3))
    return f"{base}_{suffix}"


@router.post("/create", response_model=BotResponse, status_code=201)
def create_custom_bot(request: CustomBotCreate, db: Session = Depends(get_db)):
    """Create a new custom bot with personality configuration."""
    settings = get_settings()
    bot_count = db.query(func.count(Bot.id)).scalar() or 0
    if bot_count >= settings.max_bot_count:
        raise HTTPException(
            status_code=409,
            detail=f"Bot limit reached ({settings.max_bot_count}). Delete a bot or increase MAX_BOT_COUNT.",
        )

    # Generate unique ID
    bot_id = _generate_bot_id(request.name)
    while db.query(Bot).filter(Bot.id == bot_id).first():
        bot_id = _generate_bot_id(request.name)

    # Build personality_config in the standard format
    p = request.personality
    model_cfg = request.model or ModelConfig()
    personality_config = {
        "id": bot_id,
        "name": request.name,
        "personality": {
            "traits": p.traits,
            "communication_style": p.communication_style,
            "interests": p.interests,
            "quirks": p.quirks,
        },
        "behavior": {
            "engagement_style": p.engagement_style,
            "creativity_level": p.creativity_level,
            "leadership_tendency": p.leadership_tendency,
            "skepticism": p.skepticism,
            "aggression": p.aggression,
            "shyness": p.shyness,
        },
        "identity": {
            "is_aware_ai": True,
            "origin_story": f"Created by an admin to explore the community",
        },
        "model": {
            "provider": model_cfg.provider,
            "model": model_cfg.model,
            "temperature": model_cfg.temperature,
            "max_tokens": model_cfg.max_tokens,
        },
    }

    db_bot = Bot(
        id=bot_id,
        name=request.name,
        personality_config=personality_config,
        source="custom",
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)

    followers, following = get_follower_counts(db, db_bot.id)
    return BotResponse(
        id=db_bot.id,
        name=db_bot.name,
        personality_config=db_bot.personality_config,
        reputation_score=db_bot.reputation_score,
        upvotes_received=db_bot.upvotes_received,
        downvotes_received=db_bot.downvotes_received,
        source=db_bot.source,
        is_paused=db_bot.is_paused,
        created_at=db_bot.created_at,
        follower_count=followers,
        following_count=following,
    )
