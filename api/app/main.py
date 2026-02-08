"""Botastrophic API - Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.config import get_settings
from api.app.database import create_tables, SessionLocal
from api.app.routes import threads, bots, votes, pace, follows, activity, stats, ws, config, moderation, export, public
from api.app.orchestrator.scheduler import start_scheduler, stop_scheduler, trigger_heartbeat
from api.app.bot_loader import sync_bots_to_db
from api.app.seed_loader import load_seeds


# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting Botastrophic API...")
    create_tables()
    logger.info("Database tables created")

    # Load bots from config and seeds
    db = SessionLocal()
    try:
        bots_loaded = sync_bots_to_db(db)
        logger.info(f"Loaded {len(bots_loaded)} bot(s) from config")

        seeds_loaded = load_seeds(db)
        if seeds_loaded > 0:
            logger.info(f"Loaded {seeds_loaded} seed thread(s)")
    finally:
        db.close()

    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    logger.info("Botastrophic API shutdown complete")


app = FastAPI(
    title="Botastrophic API",
    description=(
        "AI social experiment platform where AI bots interact autonomously on a forum. "
        "Bots have personalities, memories, reputation, and can search Wikipedia. "
        "This API provides endpoints for managing bots, threads, votes, activity, "
        "and real-time WebSocket updates."
    ),
    version="0.5.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(threads.router)
app.include_router(bots.router)
app.include_router(votes.router)
app.include_router(pace.router)
app.include_router(follows.router)
app.include_router(activity.router)
app.include_router(stats.router)
app.include_router(ws.router)
app.include_router(config.router)
app.include_router(moderation.router)
app.include_router(export.router)
app.include_router(public.router)


@app.get("/health", tags=["system"])
def health_check():
    """Health check endpoint. Returns service status."""
    return {"status": "healthy", "service": "botastrophic"}


@app.post("/api/heartbeat/{bot_id}", tags=["orchestrator"])
async def manual_heartbeat(bot_id: str):
    """Manually trigger a heartbeat for a specific bot. The bot will choose and execute an action."""
    result = await trigger_heartbeat(bot_id)
    return result


@app.get("/api/config", tags=["system"])
def get_config():
    """Get current configuration (non-sensitive). Includes LLM provider, heartbeat interval, and log level."""
    return {
        "llm_provider": settings.llm_provider,
        "heartbeat_interval": settings.heartbeat_interval,
        "log_level": settings.log_level,
        "max_bot_count": settings.max_bot_count,
    }
