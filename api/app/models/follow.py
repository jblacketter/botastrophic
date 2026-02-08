"""Follow model for bot relationships."""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from api.app.database import Base


class Follow(Base):
    """Follow relationship between bots."""

    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    follower_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("bots.id"), nullable=False
    )
    following_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("bots.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # One follow relationship per pair
    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='uq_follow_pair'),
    )

    def __repr__(self) -> str:
        return f"<Follow(follower={self.follower_id}, following={self.following_id})>"
