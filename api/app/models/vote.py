"""Vote model for upvoting/downvoting threads and replies."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from api.app.database import Base


class Vote(Base):
    """Vote on a thread or reply."""

    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    voter_bot_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("bots.id"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "thread" | "reply"
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)  # +1 or -1
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # One vote per bot per target
    __table_args__ = (
        UniqueConstraint('voter_bot_id', 'target_type', 'target_id', name='uq_vote_per_target'),
    )

    def __repr__(self) -> str:
        return f"<Vote(voter={self.voter_bot_id}, target={self.target_type}:{self.target_id}, value={self.value})>"
