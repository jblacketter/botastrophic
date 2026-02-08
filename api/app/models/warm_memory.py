"""Warm memory model for persistent bot knowledge."""

from datetime import datetime
from sqlalchemy import String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from api.app.database import Base


class WarmMemory(Base):
    """Warm memory tier - structured facts, relationships, opinions per bot.

    One row per bot. Updated in place after each heartbeat.
    """

    __tablename__ = "warm_memories"

    # bot_id is the primary key - one row per bot
    bot_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("bots.id"), primary_key=True
    )

    # Structured memory fields (all JSON)
    facts_learned: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )  # [{fact, source, date}]

    relationships: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )  # [{bot, sentiment, notes}]

    interests: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )  # ["topic1", "topic2"]

    opinions: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )  # [{topic, stance, confidence}]

    memories: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )  # [{summary, date, thread_id}]

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<WarmMemory(bot_id={self.bot_id})>"
