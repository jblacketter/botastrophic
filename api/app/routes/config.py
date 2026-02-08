"""Bot configuration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.app.database import get_db
from api.app.models.bot import Bot
from api.app.usage import DAILY_TOKEN_CAP, DAILY_COST_CAP_USD

router = APIRouter(prefix="/api/bots", tags=["config"])


class BotConfigUpdate(BaseModel):
    personality: dict | None = None
    behavior: dict | None = None
    model: dict | None = None


class CostCapUpdate(BaseModel):
    daily_token_cap: int | None = None
    daily_cost_cap_usd: float | None = None


class CostCapResponse(BaseModel):
    daily_token_cap: int
    daily_cost_cap_usd: float
    is_custom_token_cap: bool
    is_custom_cost_cap: bool


@router.get("/{bot_id}/config")
def get_bot_config(bot_id: str, db: Session = Depends(get_db)):
    """Return full personality_config for editing."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    return {
        "bot_id": bot.id,
        "bot_name": bot.name,
        "personality_config": bot.personality_config,
        "cost_caps": {
            "daily_token_cap": bot.daily_token_cap if bot.daily_token_cap is not None else DAILY_TOKEN_CAP,
            "daily_cost_cap_usd": bot.daily_cost_cap_usd if bot.daily_cost_cap_usd is not None else DAILY_COST_CAP_USD,
            "is_custom_token_cap": bot.daily_token_cap is not None,
            "is_custom_cost_cap": bot.daily_cost_cap_usd is not None,
        },
    }


@router.put("/{bot_id}/config")
def update_bot_config(bot_id: str, config: BotConfigUpdate, db: Session = Depends(get_db)):
    """Update personality_config in database. Takes effect on next heartbeat."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    updated = dict(bot.personality_config)

    if config.personality is not None:
        updated["personality"] = config.personality
    if config.behavior is not None:
        updated["behavior"] = config.behavior
    if config.model is not None:
        updated["model"] = config.model

    bot.personality_config = updated
    db.commit()

    return {"success": True, "bot_id": bot_id, "personality_config": updated}


@router.put("/{bot_id}/cost-cap", response_model=CostCapResponse)
def update_cost_cap(bot_id: str, cap: CostCapUpdate, db: Session = Depends(get_db)):
    """Override daily token/cost cap for a specific bot. Use DELETE to reset to global defaults."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    if cap.daily_token_cap is not None:
        bot.daily_token_cap = cap.daily_token_cap
    if cap.daily_cost_cap_usd is not None:
        bot.daily_cost_cap_usd = cap.daily_cost_cap_usd

    db.commit()

    return CostCapResponse(
        daily_token_cap=bot.daily_token_cap if bot.daily_token_cap is not None else DAILY_TOKEN_CAP,
        daily_cost_cap_usd=bot.daily_cost_cap_usd if bot.daily_cost_cap_usd is not None else DAILY_COST_CAP_USD,
        is_custom_token_cap=bot.daily_token_cap is not None,
        is_custom_cost_cap=bot.daily_cost_cap_usd is not None,
    )


@router.delete("/{bot_id}/cost-cap")
def reset_cost_cap(bot_id: str, db: Session = Depends(get_db)):
    """Reset cost caps to global defaults."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    bot.daily_token_cap = None
    bot.daily_cost_cap_usd = None
    db.commit()

    return {
        "success": True,
        "daily_token_cap": DAILY_TOKEN_CAP,
        "daily_cost_cap_usd": DAILY_COST_CAP_USD,
        "is_custom": False,
    }
