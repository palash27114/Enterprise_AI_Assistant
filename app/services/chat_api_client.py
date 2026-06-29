"""Chat orchestrator that dispatches intents to enterprise REST API handlers."""

import logging
from typing import Any

from app.services import action_service

logger = logging.getLogger(__name__)


def call_api_for_intent(intent: str, question: str, user: Any) -> dict[str, Any]:
    """
    Route a detected chat intent to the same service layer used by REST endpoints.

    This keeps POST /ask and Swagger-documented APIs in sync.
    """
    logger.info("Chat API dispatch: intent=%s", intent)
    return action_service.execute(intent, question, user_id=user.id, user=user)
