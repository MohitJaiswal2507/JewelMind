"""
SQLAlchemy Session Factory and FastAPI Dependency
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

# Configure connection arguments (e.g., for SQLite fallback or PostgreSQL)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO_LOG,
    connect_args=connect_args,
    pool_pre_ping=True,
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy session and ensuring proper teardown.
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as exc:
        db.rollback()
        logger.error(f"Database session rollback due to exception: {exc}")
        raise
    finally:
        db.close()
