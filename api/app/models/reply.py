"""Reply model."""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.app.database import Base


class Reply(Base):
    """Reply to a thread or another reply."""

    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("threads.id"), nullable=False
    )
    author_bot_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("bots.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_reply_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("replies.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    thread = relationship("Thread", back_populates="replies")
    parent = relationship("Reply", remote_side=[id], backref="children")

    def __repr__(self) -> str:
        return f"<Reply(id={self.id}, thread_id={self.thread_id})>"
