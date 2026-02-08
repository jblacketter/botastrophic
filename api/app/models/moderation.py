"""Content moderation model."""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from api.app.database import Base


class ContentFlag(Base):
    """Content flag for moderation."""

    __tablename__ = "content_flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "thread" or "reply"
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    flag_type: Mapped[str] = mapped_column(String(30), nullable=False)  # "repetitive", "off_topic", "toxic", "low_quality", "frequency"
    flagged_by: Mapped[str] = mapped_column(String(50), nullable=False)  # "auto" or bot_id
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<ContentFlag(id={self.id}, type={self.flag_type}, target={self.target_type}:{self.target_id})>"
