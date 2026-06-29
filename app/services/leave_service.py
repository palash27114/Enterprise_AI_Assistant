"""Leave request data from PostgreSQL."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.models import LeaveRequest
from app.db.session import get_session


def _leave_to_dict(leave: LeaveRequest) -> dict[str, Any]:
    return {
        "request_id": leave.request_id,
        "employee": leave.employee.name if leave.employee else leave.employee_id,
        "employee_id": leave.employee_id,
        "days": leave.days,
        "status": leave.status,
    }


def list_leave_requests() -> list[dict[str, Any]]:
    """Return all leave requests."""
    with get_session() as session:
        rows = session.scalars(
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.employee))
            .order_by(LeaveRequest.request_id)
        ).unique().all()
        return [_leave_to_dict(row) for row in rows]
