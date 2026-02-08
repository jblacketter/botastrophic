"""Cold memory model for compressed older memories."""

from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from api.app.database import Base


class ColdMemory(Base):
    """Cold memory tier - compressed summaries of older warm memories."""

    __tablename__ = "cold_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[str] = mapped_column(String(50), ForeignKey("bots.id"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_relationships: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    facts_compressed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memories_compressed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<ColdMemory(bot={self.bot_id}, period={self.period_start}..{self.period_end})>"
