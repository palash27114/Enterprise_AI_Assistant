"""Conversation memory persistence and retrieval."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import joinedload

from app.db.models import Conversation, Message
from app.db.session import get_session

logger = logging.getLogger(__name__)


class ConversationAccessError(Exception):
    """Raised when a user tries to access another user's conversation."""


def create_conversation_id() -> str:
    """Generate a unique conversation identifier."""
    return str(uuid.uuid4())


def get_conversation(conversation_id: str, user_id: str) -> dict[str, Any] | None:
    """Return a conversation by ID for a specific user."""
    with get_session() as session:
        conversation = session.get(
            Conversation,
            conversation_id,
            options=[joinedload(Conversation.messages)],
        )
        if not conversation or conversation.user_id != user_id:
            return None
        return _conversation_to_dict(conversation)


def get_or_create_conversation(conversation_id: str | None, user_id: str) -> dict[str, Any]:
    """Return an existing conversation or create a new one for the user."""
    with get_session() as session:
        if conversation_id:
            conversation = session.get(
                Conversation,
                conversation_id,
                options=[joinedload(Conversation.messages)],
            )
            if conversation:
                if conversation.user_id != user_id:
                    raise ConversationAccessError("Conversation does not belong to this user.")
                return _conversation_to_dict(conversation)

        new_id = conversation_id or create_conversation_id()
        conversation = Conversation(
            conversation_id=new_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(conversation)
        session.flush()
        logger.info("Created conversation: %s for user %s", conversation.conversation_id, user_id)
        return _conversation_to_dict(conversation)


def add_message(conversation_id: str, user_id: str, role: str, content: str) -> None:
    """Append a message to the user's conversation history."""
    with get_session() as session:
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            conversation = Conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                timestamp=datetime.now(timezone.utc),
            )
            session.add(conversation)
        elif conversation.user_id != user_id:
            raise ConversationAccessError("Conversation does not belong to this user.")

        conversation.messages.append(Message(role=role, content=content))
        conversation.timestamp = datetime.now(timezone.utc)


def get_message_history(conversation_id: str, user_id: str) -> list[dict[str, str]]:
    """Return message history for a user's conversation."""
    with get_session() as session:
        conversation = session.get(
            Conversation,
            conversation_id,
            options=[joinedload(Conversation.messages)],
        )
        if not conversation or conversation.user_id != user_id:
            return []
        return [{"role": m.role, "content": m.content} for m in conversation.messages]


def list_user_conversations(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return conversation summaries for a user, newest first."""
    from sqlalchemy import select

    with get_session() as session:
        conversations = session.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .options(joinedload(Conversation.messages))
            .order_by(Conversation.timestamp.desc())
            .limit(limit)
        ).unique().all()

        summaries: list[dict[str, Any]] = []
        for conversation in conversations:
            messages = conversation.messages
            if not messages:
                continue

            first_user = next((m.content for m in messages if m.role == "user"), None)
            last_message = messages[-1].content if messages else ""
            title = _conversation_title(first_user or last_message)

            summaries.append(
                {
                    "conversation_id": str(conversation.conversation_id),
                    "title": title,
                    "preview": last_message[:120],
                    "message_count": len(messages),
                    "updated_at": conversation.timestamp.isoformat(),
                }
            )

        return summaries


def _conversation_title(text: str, max_length: int = 48) -> str:
    """Build a short conversation title from the first user message."""
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return "New conversation"
    if len(cleaned) <= max_length:
        return cleaned
    return f"{cleaned[: max_length - 1].rstrip()}…"


def _conversation_to_dict(conversation: Conversation) -> dict[str, Any]:
    """Convert a Conversation ORM object to the API dict format."""
    return {
        "conversation_id": str(conversation.conversation_id),
        "messages": [{"role": m.role, "content": m.content} for m in conversation.messages],
        "timestamp": conversation.timestamp.isoformat(),
    }
