"""Support ticket creation and persistence."""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db.models import Ticket, User
from app.db.session import get_session
from app.services import employee_service

logger = logging.getLogger(__name__)

VALID_STATUSES = frozenset({"Open", "In Progress", "Resolved", "Closed"})
VALID_PRIORITIES = frozenset({"Low", "Medium", "High"})


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


def _ticket_to_dict(ticket: Ticket) -> dict[str, Any]:
    """Serialize a ticket ORM record."""
    return {
        "id": ticket.id,
        "issue": ticket.issue,
        "status": ticket.status,
        "priority": ticket.priority,
        "user_id": ticket.user_id,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else ticket.created_at.isoformat(),
    }


def create_ticket(issue: str, user_id: str | None = None, priority: str = "Medium") -> dict[str, Any]:
    """Create a new support ticket and persist it."""
    normalized_priority = priority if priority in VALID_PRIORITIES else "Medium"

    with get_session() as session:
        ticket = Ticket(
            id=_next_ticket_id(session),
            issue=issue,
            status="Open",
            priority=normalized_priority,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(ticket)
        session.flush()
        ticket_data = _ticket_to_dict(ticket)

    logger.info("Ticket created: %s - %s", ticket_data["id"], ticket_data["issue"])
    return ticket_data


def get_ticket(ticket_id: str) -> dict[str, Any] | None:
    """Fetch a ticket by ID."""
    with get_session() as session:
        ticket = session.get(Ticket, ticket_id.upper())
        if not ticket:
            return None
        return _ticket_to_dict(ticket)


def _ticket_query_row(ticket: Ticket) -> dict[str, Any]:
    """Serialize a ticket for query results."""
    return {
        "ticket_id": ticket.id,
        "issue": ticket.issue,
        "status": ticket.status,
        "priority": ticket.priority,
    }


def list_tickets(user: User | None = None) -> list[dict[str, Any]]:
    """List tickets visible to the user (all for HR/executive, own tickets otherwise)."""
    with get_session() as session:
        query = select(Ticket).order_by(Ticket.updated_at.desc())

        if user is not None:
            employee = employee_service.get_employee_for_user(user)
            access_role = employee["access_role"] if employee else None
            if access_role not in {"hr", "executive"}:
                query = query.where(Ticket.user_id == user.id)

        tickets = session.scalars(query).all()
        return [_ticket_query_row(ticket) for ticket in tickets]


def list_tickets_for_user(user_id: str) -> list[dict[str, Any]]:
    """List tickets owned by a user."""
    with get_session() as session:
        tickets = session.scalars(
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.updated_at.desc())
        ).all()
        return [_ticket_to_dict(ticket) for ticket in tickets]


def update_ticket(
    ticket_id: str,
    user_id: str,
    *,
    issue: str | None = None,
    status: str | None = None,
    priority: str | None = None,
) -> dict[str, Any] | None:
    """Update ticket fields for the owning user."""
    with get_session() as session:
        ticket = session.get(Ticket, ticket_id.upper())
        if not ticket or ticket.user_id != user_id:
            return None

        if issue is not None:
            ticket.issue = issue.strip()
        if status is not None:
            if status not in VALID_STATUSES:
                raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(VALID_STATUSES))}")
            ticket.status = status
        if priority is not None:
            if priority not in VALID_PRIORITIES:
                raise ValueError(f"Invalid priority. Allowed: {', '.join(sorted(VALID_PRIORITIES))}")
            ticket.priority = priority

        ticket.updated_at = datetime.now(timezone.utc)
        session.flush()
        ticket_data = _ticket_to_dict(ticket)

    logger.info("Ticket updated: %s", ticket_id)
    return ticket_data
