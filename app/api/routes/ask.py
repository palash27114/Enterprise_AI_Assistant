"""Assistant ask route."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import get_current_user
from app.db.models import User
from app.models.openapi import ASK_RESPONSES
from app.models.schemas import AgentListResponse, AskRequest, AskResponse
from app.services import agent_service, llm_service, memory_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Assistant"])


@router.get(
    "/agents",
    response_model=AgentListResponse,
    summary="List available AI agents",
    description="Returns configured LLM providers (OpenAI, Gemini) and whether each is available.",
)
async def list_agents() -> AgentListResponse:
    """Return available AI agents."""
    agents = agent_service.get_available_agents()
    default_agent = agent_service.pick_preferred_agent(agents)
    return AgentListResponse(default_agent=default_agent, agents=agents)


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the enterprise AI assistant",
    description="""
Process a natural-language message. The AI decides whether to answer directly or call
an enterprise API (profile, tickets, reports, lookups, queries, workflows).

**Authentication required** — include `Authorization: Bearer <access_token>`.
    """,
    responses={
        **ASK_RESPONSES,
        401: {"description": "Missing or invalid access token."},
    },
    status_code=status.HTTP_200_OK,
)
async def ask(
    payload: AskRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    x_conversation_id: Annotated[
        Optional[str],
        Header(
            alias="X-Conversation-Id",
            description="Optional conversation UUID from a previous `/ask` response.",
            examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
        ),
    ] = None,
) -> AskResponse:
    """Process a user message through the AI assistant with intelligent tool routing."""
    question = payload.question
    selected_agent = payload.agent
    logger.info(
        "Incoming request from %s: agent=%s question=%r",
        current_user.email,
        selected_agent or "default",
        question[:120],
    )

    try:
        conversation = memory_service.get_or_create_conversation(
            x_conversation_id,
            current_user.id,
        )
    except memory_service.ConversationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    conversation_id = str(conversation["conversation_id"])
    memory_service.add_message(conversation_id, current_user.id, "user", question)

    history = memory_service.get_message_history(conversation_id, current_user.id)
    history_without_current = history[:-1] if history else []

    try:
        result = llm_service.process_assistant_request(
            question,
            history_without_current,
            current_user,
            provider=selected_agent,
        )
        memory_service.add_message(conversation_id, current_user.id, "assistant", result["response"])

        return AskResponse(
            response=result["response"],
            action=result["action"],
            ticket_id=result.get("ticket_id"),
            conversation_id=conversation_id,
            status=result.get("status"),
            data=result.get("data"),
            agent=result.get("agent"),
        )
    except llm_service.LLMServiceError as exc:
        logger.error("LLM service error: %s", exc)
        fallback = str(exc) or "AI service unavailable. Please try again later."
        memory_service.add_message(conversation_id, current_user.id, "assistant", fallback)

        return AskResponse(
            response=fallback,
            action="error",
            conversation_id=conversation_id,
            agent=selected_agent,
        )
    except Exception as exc:
        logger.exception("Unexpected error while processing request: %s", exc)
        fallback = "AI service unavailable. Please try again later."

        return AskResponse(
            response=fallback,
            action="error",
            conversation_id=conversation_id,
            agent=selected_agent,
        )
