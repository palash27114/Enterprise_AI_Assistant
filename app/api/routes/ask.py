"""Assistant ask route."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Header, status

from app.models.openapi import ASK_RESPONSES
from app.models.schemas import AskRequest, AskResponse
from app.services import intent, llm_service, memory_service, ticket_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Assistant"])


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a question or create a support ticket",
    description="""
Process a user question through the enterprise assistant pipeline:

1. **Validate** the question (non-empty, max 1000 characters).
2. **Store** the message in conversation history.
3. **Detect intent** — ticket keywords trigger automatic ticket creation; otherwise the LLM is called.
4. **Return** a structured response with `action`, `conversation_id`, and optional `ticket_id` / `status`.

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | Must be `application/json` |
| `X-Conversation-Id` | No | UUID from a previous response to continue the same conversation |

### Ticket keywords

Questions containing any of these words create a support ticket:
`ticket`, `issue`, `problem`, `incident`, `laptop`, `outlook`, `vpn`, `access`, `login`.
    """,
    responses=ASK_RESPONSES,
    status_code=status.HTTP_200_OK,
)
async def ask(
    payload: AskRequest,
    x_conversation_id: Annotated[
        Optional[str],
        Header(
            alias="X-Conversation-Id",
            description=(
                "Optional conversation UUID from a previous `/ask` response. "
                "When provided, prior messages are included in the LLM context."
            ),
            examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
        ),
    ] = None,
) -> AskResponse:
    """Process a user question: route to ticket creation or LLM response."""
    question = payload.question
    logger.info("Incoming request: question=%r", question[:120])

    conversation = memory_service.get_or_create_conversation(x_conversation_id)
    conversation_id = conversation["conversation_id"]

    memory_service.add_message(conversation_id, "user", question)

    detected_intent = intent.detect_intent(question)

    if detected_intent == "create_ticket":
        ticket = ticket_service.create_ticket(question)
        response_text = "Support ticket created successfully."
        memory_service.add_message(conversation_id, "assistant", response_text)

        return AskResponse(
            response=response_text,
            action="create_ticket",
            ticket_id=ticket["id"],
            conversation_id=conversation_id,
            status=ticket["status"],
        )

    history = memory_service.get_message_history(conversation_id)
    history_without_current = history[:-1] if history else []

    try:
        ai_response = llm_service.generate_response(question, history_without_current)
        memory_service.add_message(conversation_id, "assistant", ai_response)

        return AskResponse(
            response=ai_response,
            action="ai_response",
            conversation_id=conversation_id,
        )
    except llm_service.LLMServiceError as exc:
        logger.error("LLM service error: %s", exc)
        fallback = "AI service unavailable. Please try again later."
        memory_service.add_message(conversation_id, "assistant", fallback)

        return AskResponse(
            response=fallback,
            action="error",
            conversation_id=conversation_id,
        )
    except Exception as exc:
        logger.exception("Unexpected error while processing request: %s", exc)
        fallback = "AI service unavailable. Please try again later."

        return AskResponse(
            response=fallback,
            action="error",
            conversation_id=conversation_id,
        )
