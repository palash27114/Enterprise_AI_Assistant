"""Database engine, session management, and initialization."""

import logging
import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATABASE_URL
from app.db.migrations import run_migrations

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(max_retries: int = 10, retry_delay: float = 3.0) -> None:
    """Run Liquibase-compatible migrations and verify database connectivity."""
    run_migrations(engine, max_retries=max_retries, retry_delay=retry_delay)

    for attempt in range(1, max_retries + 1):
        try:
            with get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database initialized successfully")
            return
        except OperationalError as exc:
            if attempt == max_retries:
                logger.error("Database connection failed after %s attempts: %s", max_retries, exc)
                raise
            logger.warning(
                "Database not ready (attempt %s/%s), retrying in %ss...",
                attempt,
                max_retries,
                retry_delay,
            )
            time.sleep(retry_delay)


def check_database() -> bool:
    """Return True if the database is reachable."""
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return False
