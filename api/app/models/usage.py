"""Token usage tracking model."""

from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from api.app.database import Base


class TokenUsage(Base):
    """Track per-bot daily token usage and estimated cost."""

    __tablename__ = "token_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[str] = mapped_column(String(50), ForeignKey("bots.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<TokenUsage(bot={self.bot_id}, date={self.date}, tokens={self.input_tokens + self.output_tokens})>"
