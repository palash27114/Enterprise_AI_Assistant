"""Query enterprise tables stored in PostgreSQL."""

from datetime import datetime, timezone
from typing import Any

from app.db.models import Policy, User
from app.db.session import get_session
from app.services import customer_service, employee_service, leave_service, ticket_service
from sqlalchemy import select


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _list_policies() -> list[dict[str, Any]]:
    with get_session() as session:
        policies = session.scalars(select(Policy).order_by(Policy.id)).all()
        return [{"section": policy.section, "summary": policy.summary} for policy in policies]


def _rows_for_table(table_name: str, user: User | None) -> list[dict[str, Any]]:
    normalized = table_name.lower().replace(".csv", "")

    if normalized in {"employees", "employee"}:
        if user is None:
            return employee_service.list_all_employees()
        return employee_service.list_visible_employees(user)

    if normalized in {"customers", "customer"}:
        return customer_service.list_customers()

    if normalized in {"tickets", "ticket", "incidents", "incident"}:
        return ticket_service.list_tickets(user)

    if normalized in {"leave_requests", "leave", "leaves"}:
        return leave_service.list_leave_requests()

    if normalized in {"policies", "policies.txt", "policy"}:
        return _list_policies()

    return []


def resolve_query_target(question: str) -> tuple[str, str]:
    """Pick a database table from natural language."""
    lowered = question.lower()

    if "polic" in lowered or "policies.txt" in lowered:
        return "database", "policies"
    if "leave" in lowered:
        return "database", "leave_requests"
    if "ticket" in lowered or "incident" in lowered:
        return "database", "tickets"
    if "customer" in lowered or "client" in lowered:
        return "database", "customers"
    if "employee" in lowered or "staff" in lowered or "people" in lowered or "headcount" in lowered:
        return "database", "employees"
    if "file" in lowered or "csv" in lowered:
        return "database", "employees"

    return "database", "employees"


def run_query(
    *,
    user: User | None = None,
    source_type: str | None = None,
    source_name: str | None = None,
    question: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Query a supported enterprise table."""
    if source_type == "file":
        source_type = "database"
        if source_name and source_name.endswith(".csv"):
            source_name = source_name.replace(".csv", "")

    if source_type and source_name:
        resolved_type = source_type
        resolved_name = source_name
    else:
        resolved_type, resolved_name = resolve_query_target(question or "")

    rows = _rows_for_table(resolved_name, user)
    return {
        "source_type": resolved_type,
        "source_name": resolved_name,
        "row_count": len(rows),
        "rows": rows[:limit],
        "executed_at": _utc_now_iso(),
    }
