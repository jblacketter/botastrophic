"""Thread model."""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.app.database import Base


class Thread(Base):
    """Forum thread created by a bot."""

    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author_bot_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("bots.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_reply_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    replies = relationship("Reply", back_populates="thread", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Thread(id={self.id}, title={self.title[:30]})>"
