"""Application logging configuration."""

import logging

from app.core.config import LOG_LEVEL


def setup_logging() -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
