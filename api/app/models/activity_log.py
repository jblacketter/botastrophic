"""Activity log model for tracking bot actions."""

from datetime import datetime
from sqlalchemy import String, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from api.app.database import Base


class ActivityLog(Base):
    """Log of bot actions for monitoring and memory."""

    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bot_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("bots.id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, bot_id={self.bot_id}, action={self.action_type})>"
