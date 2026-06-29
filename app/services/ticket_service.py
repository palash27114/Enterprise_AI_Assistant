"""Support ticket creation and persistence."""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db.models import Ticket
from app.db.session import get_session

logger = logging.getLogger(__name__)


def _next_ticket_id(session) -> str:
    """Generate the next sequential incident ID."""
    ticket_ids = session.scalars(select(Ticket.id)).all()
    max_number = 1000
    pattern = re.compile(r"^INC-(\d+)$")

    for ticket_id in ticket_ids:
        match = pattern.match(ticket_id)
        if match:
            max_number = max(max_number, int(match.group(1)))

    return f"INC-{max_number + 1}"


def create_ticket(issue: str, user_id: str | None = None) -> dict[str, Any]:
    """Create a new support ticket and persist it."""
    with get_session() as session:
        ticket = Ticket(
            id=_next_ticket_id(session),
            issue=issue,
            status="Open",
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
        session.add(ticket)
        session.flush()

        ticket_data = {
            "id": ticket.id,
            "issue": ticket.issue,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat(),
        }

    logger.info("Ticket created: %s - %s", ticket_data["id"], ticket_data["issue"])
    return ticket_data
