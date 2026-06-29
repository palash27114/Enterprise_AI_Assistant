"""Enterprise reports computed from live database metrics."""

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select

from app.db.models import Customer, Employee, LeaveRequest, Ticket
from app.db.session import get_session

REPORT_TYPES = frozenset({"hr", "sales", "it", "leave"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hr_metrics(session) -> dict[str, Any]:
    total = session.scalar(select(func.count()).select_from(Employee)) or 0
    departments = session.scalar(select(func.count(func.distinct(Employee.department)))) or 0
    active = session.scalar(
        select(func.count()).select_from(Employee).where(Employee.status == "Active")
    ) or 0

    today = date.today()
    employees = session.scalars(select(Employee.start_date).where(Employee.start_date.is_not(None))).all()
    tenures = [(today - start).days / 365.25 for start in employees if isinstance(start, date)]
    avg_tenure = round(sum(tenures) / len(tenures), 1) if tenures else 0.0

    return {
        "total_employees": total,
        "active_employees": active,
        "departments": departments,
        "avg_tenure_years": avg_tenure,
    }


def _sales_metrics(session) -> dict[str, Any]:
    total_mrr = session.scalar(select(func.coalesce(func.sum(Customer.mrr_usd), 0))) or 0
    active_customers = session.scalar(
        select(func.count()).select_from(Customer).where(Customer.status == "Active")
    ) or 0
    total_customers = session.scalar(select(func.count()).select_from(Customer)) or 0
    trial_customers = session.scalar(
        select(func.count()).select_from(Customer).where(Customer.status == "Trial")
    ) or 0

    return {
        "total_mrr_usd": int(total_mrr),
        "active_customers": active_customers,
        "total_customers": total_customers,
        "trial_customers": trial_customers,
    }


def _it_metrics(session) -> dict[str, Any]:
    open_tickets = session.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.status == "Open")
    ) or 0
    in_progress = session.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.status == "In Progress")
    ) or 0
    resolved = session.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.status.in_(("Resolved", "Closed")))
    ) or 0
    critical = session.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.priority == "High")
    ) or 0

    return {
        "open_tickets": open_tickets,
        "in_progress_tickets": in_progress,
        "resolved_tickets": resolved,
        "high_priority_tickets": critical,
    }


def _leave_metrics(session) -> dict[str, Any]:
    pending = session.scalar(
        select(func.count()).select_from(LeaveRequest).where(LeaveRequest.status == "Pending")
    ) or 0
    approved = session.scalar(
        select(func.count()).select_from(LeaveRequest).where(LeaveRequest.status == "Approved")
    ) or 0
    total_days = session.scalar(select(func.coalesce(func.sum(LeaveRequest.days), 0))) or 0
    total_requests = session.scalar(select(func.count()).select_from(LeaveRequest)) or 0
    avg_days = round(total_days / total_requests, 1) if total_requests else 0.0

    return {
        "pending_requests": pending,
        "approved_requests": approved,
        "total_requests": total_requests,
        "avg_days_requested": avg_days,
    }


_REPORT_BUILDERS = {
    "hr": ("HR Headcount Report", _hr_metrics),
    "sales": ("Sales Performance Report", _sales_metrics),
    "it": ("IT Incident Report", _it_metrics),
    "leave": ("Leave Utilization Report", _leave_metrics),
}


def generate_report(report_type: str = "hr", period: str = "current_quarter") -> dict[str, Any]:
    """Build a report from live database aggregates."""
    normalized = report_type if report_type in REPORT_TYPES else "hr"
    title, builder = _REPORT_BUILDERS[normalized]

    with get_session() as session:
        metrics = builder(session)

    report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
    return {
        "report_id": report_id,
        "title": title,
        "type": normalized,
        "generated_at": _utc_now_iso(),
        "metrics": metrics,
        "format": "pdf",
        "download_url": f"/reports/{report_id}.pdf",
        "period": period,
    }
