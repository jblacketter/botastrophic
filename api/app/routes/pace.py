"""Pace control API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.app.config import get_settings
from api.app.orchestrator.scheduler import update_pace, get_current_pace, trigger_heartbeat


router = APIRouter(prefix="/api/pace", tags=["pace"])


# Pace presets in seconds
PACE_PRESETS = {
    "slow": 14400,    # 4 hours
    "normal": 3600,   # 1 hour
    "fast": 900,      # 15 minutes
    "turbo": 300,     # 5 minutes
}


class PaceResponse(BaseModel):
    preset: str
    interval_seconds: int
    interval_human: str


class PaceUpdate(BaseModel):
    preset: str


def seconds_to_human(seconds: int) -> str:
    """Convert seconds to human-readable string."""
    if seconds >= 3600:
        hours = seconds / 3600
        return f"{hours:.1f} hours" if hours != int(hours) else f"{int(hours)} hours"
    elif seconds >= 60:
        minutes = seconds / 60
        return f"{int(minutes)} minutes"
    else:
        return f"{seconds} seconds"


@router.get("", response_model=PaceResponse)
def get_pace():
    """Get current pace setting."""
    current = get_current_pace()

    # Find matching preset
    preset = "custom"
    for name, interval in PACE_PRESETS.items():
        if interval == current:
            preset = name
            break

    return PaceResponse(
        preset=preset,
        interval_seconds=current,
        interval_human=seconds_to_human(current),
    )


@router.put("", response_model=PaceResponse)
def set_pace(pace: PaceUpdate):
    """Update pace setting."""
    preset = pace.preset.lower()

    if preset not in PACE_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset. Must be one of: {', '.join(PACE_PRESETS.keys())}"
        )

    interval = PACE_PRESETS[preset]
    update_pace(interval)

    return PaceResponse(
        preset=preset,
        interval_seconds=interval,
        interval_human=seconds_to_human(interval),
    )


@router.post("/trigger/{bot_id}")
async def trigger_bot_heartbeat(bot_id: str):
    """Manually trigger a heartbeat for a specific bot."""
    result = await trigger_heartbeat(bot_id)
    return result


@router.post("/trigger")
async def trigger_all_heartbeats():
    """Manually trigger heartbeats for all bots."""
    from api.app.orchestrator.scheduler import run_all_heartbeats
    await run_all_heartbeats()
    return {"status": "ok", "message": "All heartbeats triggered"}


@router.get("/presets")
def get_presets():
    """Get available pace presets."""
    return {
        name: {
            "interval_seconds": interval,
            "interval_human": seconds_to_human(interval),
        }
        for name, interval in PACE_PRESETS.items()
    }
