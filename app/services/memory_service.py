"""Conversation memory persistence and retrieval."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import joinedload

from app.db.models import Conversation, Message
from app.db.session import get_session

logger = logging.getLogger(__name__)


def create_conversation_id() -> str:
    """Generate a unique conversation identifier."""
    return str(uuid.uuid4())


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    """Return a conversation by ID, or None if not found."""
    with get_session() as session:
        conversation = session.get(
            Conversation,
            conversation_id,
            options=[joinedload(Conversation.messages)],
        )
        if not conversation:
            return None
        return _conversation_to_dict(conversation)


def get_or_create_conversation(conversation_id: str | None = None) -> dict[str, Any]:
    """Return an existing conversation or create a new one."""
    with get_session() as session:
        if conversation_id:
            conversation = session.get(
                Conversation,
                conversation_id,
                options=[joinedload(Conversation.messages)],
            )
            if conversation:
                return _conversation_to_dict(conversation)

        new_id = conversation_id or create_conversation_id()
        conversation = Conversation(
            conversation_id=new_id,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(conversation)
        session.flush()
        logger.info("Created conversation: %s", conversation.conversation_id)
        return _conversation_to_dict(conversation)


def add_message(conversation_id: str, role: str, content: str) -> None:
    """Append a message to the conversation history."""
    with get_session() as session:
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            conversation = Conversation(
                conversation_id=conversation_id,
                timestamp=datetime.now(timezone.utc),
            )
            session.add(conversation)

        conversation.messages.append(Message(role=role, content=content))
        conversation.timestamp = datetime.now(timezone.utc)


def get_message_history(conversation_id: str) -> list[dict[str, str]]:
    """Return message history for a conversation."""
    with get_session() as session:
        conversation = session.get(
            Conversation,
            conversation_id,
            options=[joinedload(Conversation.messages)],
        )
        if not conversation:
            return []
        return [{"role": m.role, "content": m.content} for m in conversation.messages]


def _conversation_to_dict(conversation: Conversation) -> dict[str, Any]:
    """Convert a Conversation ORM object to the API dict format."""
    return {
        "conversation_id": conversation.conversation_id,
        "messages": [{"role": m.role, "content": m.content} for m in conversation.messages],
        "timestamp": conversation.timestamp.isoformat(),
    }
