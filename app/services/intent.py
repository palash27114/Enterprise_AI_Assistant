"""Intent routing between AI responses and business actions."""

import logging
import re

from app.core.config import TICKET_KEYWORDS

logger = logging.getLogger(__name__)

Intent = str


def _tokenize(text: str) -> set[str]:
    """Split text into lowercase word tokens."""
    return set(re.findall(r"[a-zA-Z]+", text.lower()))


def detect_intent(question: str) -> Intent:
    """
    Determine whether the question is a ticket request or a general AI question.

    A ticket is created when the question contains any configured keyword.
    """
    tokens = _tokenize(question)
    matched = TICKET_KEYWORDS.intersection(tokens)

    if matched:
        logger.info("Detected intent: create_ticket (keywords=%s)", sorted(matched))
        return "create_ticket"

    logger.info("Detected intent: ai_response")
    return "ai_response"
