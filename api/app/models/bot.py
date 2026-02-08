"""Bot model."""

from datetime import datetime
from sqlalchemy import String, DateTime, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from api.app.database import Base


class Bot(Base):
    """AI bot entity with personality configuration."""

    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    personality_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reputation_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upvotes_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downvotes_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_token_cap: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    daily_cost_cap_usd: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    source: Mapped[str] = mapped_column(String(20), default="yaml", nullable=False)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Bot(id={self.id}, name={self.name}, rep={self.reputation_score})>"
