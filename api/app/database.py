"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from api.app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


settings = get_settings()

# Create engine with SQLite-specific settings
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
    echo=settings.log_level == "DEBUG",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    _run_migrations()


def _run_migrations():
    """Add new columns to existing tables (SQLite doesn't auto-add on create_all)."""
    import logging
    from sqlalchemy import text, inspect

    logger = logging.getLogger(__name__)
    inspector = inspect(engine)

    migrations = [
        ("bots", "source", "VARCHAR(20) NOT NULL DEFAULT 'yaml'"),
        ("bots", "is_paused", "BOOLEAN NOT NULL DEFAULT 0"),
        ("threads", "last_reply_at", "DATETIME"),
    ]

    with engine.begin() as conn:
        for table, column, col_type in migrations:
            if table not in inspector.get_table_names():
                continue
            existing = [c["name"] for c in inspector.get_columns(table)]
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                logger.info(f"Migration: added {table}.{column}")
            else:
                logger.debug(f"Migration: {table}.{column} already exists")
