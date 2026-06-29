"""Conversation history routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.db.models import User
from app.models.schemas import ConversationDetailResponse, ConversationSummary
from app.services import memory_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get(
    "",
    response_model=list[ConversationSummary],
    summary="List user conversations",
    description="Returns the signed-in user's chat history, newest first.",
)
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ConversationSummary]:
    """List conversation summaries for the current user."""
    items = memory_service.list_user_conversations(current_user.id)
    return [ConversationSummary(**item) for item in items]


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation messages",
)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationDetailResponse:
    """Return full message history for one conversation."""
    conversation = memory_service.get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    first_user = next(
        (message["content"] for message in conversation["messages"] if message["role"] == "user"),
        None,
    )
    title = memory_service._conversation_title(first_user or "New conversation")

    return ConversationDetailResponse(
        conversation_id=conversation["conversation_id"],
        title=title,
        updated_at=conversation["timestamp"],
        messages=conversation["messages"],
    )
