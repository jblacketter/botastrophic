"""Activity log API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.app.database import get_db
from api.app.models.activity_log import ActivityLog


router = APIRouter(prefix="/api/activity", tags=["activity"])


class ActivityResponse(BaseModel):
    id: int
    bot_id: str
    action_type: str
    details: dict
    tokens_used: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[ActivityResponse])
def list_activity(
    skip: int = 0,
    limit: int = 20,
    bot_id: str | None = None,
    db: Session = Depends(get_db),
):
    """List recent activity with optional bot filter."""
    query = db.query(ActivityLog)

    if bot_id:
        query = query.filter(ActivityLog.bot_id == bot_id)

    activity = (
        query
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return activity
